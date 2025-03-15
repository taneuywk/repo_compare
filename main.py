import streamlit as st
import os
import shutil
import difflib
import git

# ----- ตั้งค่าหน้าตา Streamlit ----- #
st.set_page_config(
    page_title="Git Compare - Remove Old Folder on URL Change", layout="wide"
)
st.title(
    "🔍 Git Repository Compare - Branch or Tag, Dark Theme, Folder Remove on URL Change"
)


# ----- ฟังก์ชันลบโฟลเดอร์เก่า ----- #
def remove_dir(path: str):
    """ลบโฟลเดอร์ (recursive)"""
    if os.path.exists(path):
        shutil.rmtree(path)


# ----- ฟังก์ชัน Cache ต่าง ๆ ----- #
@st.cache_data
def clone_repo_if_not_exists(repo_url: str, repo_dir: str):
    """Clone ถ้าโฟลเดอร์ยังไม่มี"""
    if not os.path.exists(repo_dir):
        git.Repo.clone_from(repo_url, repo_dir)
    return True


@st.cache_data
def get_all_branches_and_tags(repo_dir: str):
    """ดึงรายการ Branch/Tag จาก Local Repo"""
    repo = git.Repo(repo_dir)
    branches = [str(b) for b in repo.branches]
    tags = [str(t) for t in repo.tags]
    return branches, tags


@st.cache_data
def list_files_in_ref(repo_dir: str, ref: str):
    """ดึงรายชื่อไฟล์ใน Branch หรือ Tag (เรียก 'ref')"""
    repo = git.Repo(repo_dir)
    file_list = repo.git.ls_tree("-r", "--name-only", ref).split("\n")
    return set(file_list)


@st.cache_data
def get_file_content(repo_dir: str, ref: str, file_path: str) -> str:
    """ดึงเนื้อหาไฟล์จาก ref (Branch/Tag)"""
    repo = git.Repo(repo_dir)
    try:
        return repo.git.show(f"{ref}:{file_path}")
    except git.exc.GitCommandError:
        return ""


@st.cache_data
def quick_diff_lines(content1: str, content2: str) -> int:
    """นับบรรทัดที่ต่างกันแบบเร็ว (ไม่ต้องสร้าง Side-by-Side Diff)"""
    if not content1 or not content2:
        return 0
    diffs = list(difflib.ndiff(content1.splitlines(), content2.splitlines()))
    changed = sum(1 for d in diffs if d.startswith("+") or d.startswith("-"))
    return changed


@st.cache_data
def make_side_by_side_diff(content1: str, content2: str, desc1: str, desc2: str) -> str:
    """สร้าง Diff แบบ Side-by-Side (HTML)"""
    differ = difflib.HtmlDiff(wrapcolumn=80, tabsize=4)
    return differ.make_file(
        content1.splitlines(),
        content2.splitlines(),
        fromdesc=desc1,
        todesc=desc2,
        context=False,
        numlines=0,
    )


# ========== 1) ตรวจจับ URL เปลี่ยน + ลบโฟลเดอร์เดิม + Clear cache ========== #
if "old_repo_url" not in st.session_state:
    st.session_state.old_repo_url = ""

repo_url = st.text_input("📂 Git Repository URL:", "git repo url")
repo_dir = "./git_repo"

if repo_url != st.session_state.old_repo_url and st.session_state.old_repo_url != "":
    # URL เปลี่ยน => ลบโฟลเดอร์ + clear cache
    st.warning(
        f"Repo URL changed from {st.session_state.old_repo_url} to {repo_url}. Removing old folder & clearing cache."
    )
    remove_dir(repo_dir)
    st.cache_data.clear()

st.session_state.old_repo_url = repo_url

# ===== ปุ่ม Reload Cache ด้วยตัวเอง ===== #
if st.button("Reload Cache"):
    st.cache_data.clear()
    st.success("Cache cleared manually!")

# ===== ปุ่ม Clone ===== #
if st.button("Clone Repository"):
    with st.spinner("Cloning or Checking..."):
        clone_repo_if_not_exists(repo_url, repo_dir)
    st.success("Repository is ready!")

# ===== ถ้ามีโฟลเดอร์แล้ว => ดึง Branch/Tag ===== #
if os.path.exists(repo_dir):
    branches, tags = get_all_branches_and_tags(repo_dir)
    # ถ้ายังไม่มี Branch/Tag แปลว่า Repo อาจว่างหรือผิด
    if not branches and not tags:
        st.error("No Branches or Tags found in this repository.")
    else:
        # ----- สร้าง Radio Button ฝั่งซ้าย ว่าจะเทียบ Branch / Tag ----- #
        st.subheader("Compare Side 1")
        compare_type_1 = st.radio(
            "Compare type 1", ["Branch", "Tag"], index=0, horizontal=True
        )
        if compare_type_1 == "Branch":
            ref_list_1 = branches
        else:
            ref_list_1 = tags

        # Drop-down เลือกชื่อ Branch/Tag ตาม Radio
        side1 = (
            st.selectbox("Select side 1", ref_list_1, key="side1_select")
            if ref_list_1
            else None
        )

        # ----- สร้าง Radio Button ฝั่งขวา ว่าจะเทียบ Branch / Tag ----- #
        st.subheader("Compare Side 2")
        compare_type_2 = st.radio(
            "Compare type 2", ["Branch", "Tag"], index=0, horizontal=True
        )
        if compare_type_2 == "Branch":
            ref_list_2 = branches
        else:
            ref_list_2 = tags

        side2 = (
            st.selectbox("Select side 2", ref_list_2, key="side2_select")
            if ref_list_2
            else None
        )

        # ----- ถ้ามี ref ทั้ง 2 ฝั่ง ----- #
        if side1 and side2:
            # ดึงรายชื่อไฟล์
            files_side1 = list_files_in_ref(repo_dir, side1)
            files_side2 = list_files_in_ref(repo_dir, side2)

            only_in_side1 = files_side1 - files_side2
            only_in_side2 = files_side2 - files_side1
            common_files = files_side1.intersection(files_side2)

            st.subheader("📁 Folder & File Structure Differences")
            col_left, col_right = st.columns(2)

            with col_left:
                st.write(f"Files only in `{side1}`:")
                if only_in_side1:
                    st.code("\n".join(sorted(only_in_side1)))
                else:
                    st.write("— None —")

            with col_right:
                st.write(f"Files only in `{side2}`:")
                if only_in_side2:
                    st.code("\n".join(sorted(only_in_side2)))
                else:
                    st.write("— None —")

            # ----- Custom File Mapping ----- #
            if "file_mapping" not in st.session_state:
                st.session_state.file_mapping = {}

            st.subheader("🔗 Custom File Mapping (ชื่อไฟล์ไม่ตรงกัน)")
            with st.form("custom_mapping_form", clear_on_submit=True):
                f_in_1 = st.text_input(f"File name in {side1}")
                f_in_2 = st.text_input(f"File name in {side2}")
                submitted_map = st.form_submit_button("Add Mapping")
                if submitted_map:
                    if f_in_1 and f_in_2:
                        st.session_state.file_mapping[f_in_1] = f_in_2
                        st.success(f"Added mapping: {f_in_1} => {f_in_2}")
                    else:
                        st.warning("Please fill both file names before adding mapping.")

            if st.session_state.file_mapping:
                st.write("Current Mappings:")
                for k, v in st.session_state.file_mapping.items():
                    st.text(f"{k} => {v}")
            else:
                st.write("No custom file mappings yet.")

            # ----- รวมไฟล์ที่จะเทียบ (common + mapping) ----- #
            compare_pairs = {}
            for f in common_files:
                compare_pairs[f] = f
            for old_name, new_name in st.session_state.file_mapping.items():
                compare_pairs[old_name] = new_name

            # ----- Partial Diff: สรุปไฟล์ที่ต่าง ----- #
            summary_data = []
            for f1, f2 in compare_pairs.items():
                content1 = get_file_content(repo_dir, side1, f1)
                content2 = get_file_content(repo_dir, side2, f2)
                if content1 and content2 and (content1 != content2):
                    changed = quick_diff_lines(content1, content2)
                    if changed > 0:
                        summary_data.append(
                            {"file1": f1, "file2": f2, "changed_lines": changed}
                        )

            if summary_data:
                st.subheader("📝 Differences Summary")
                st.table(summary_data)

                # Selectbox สำหรับเลือกไฟล์คู่
                pair_display_list = [
                    f"{item['file1']} => {item['file2']} (Changed {item['changed_lines']} lines)"
                    for item in summary_data
                ]
                selected_pair_str = st.selectbox(
                    "📄 Select File Pair to Compare:", pair_display_list
                )

                # แปลงกลับเพื่อเข้าถึง content
                reverse_map = {}
                for item in summary_data:
                    disp = f"{item['file1']} => {item['file2']} (Changed {item['changed_lines']} lines)"
                    reverse_map[disp] = (item["file1"], item["file2"])

                file1, file2 = reverse_map[selected_pair_str]
                c1 = get_file_content(repo_dir, side1, file1)
                c2 = get_file_content(repo_dir, side2, file2)

                st.subheader(f"🔍 Side-by-Side Diff: {file1} => {file2}")

                html_diff = make_side_by_side_diff(
                    c1, c2, f"{side1}:{file1}", f"{side2}:{file2}"
                )

                # ----- CSS Dark Theme + ตัวอักษรขาวหนา ----- #
                custom_css = """
                <style>
                table.diff {
                  width: 100%;
                  border-collapse: collapse;
                  font-family: Consolas, "Courier New", monospace;
                  background-color: #1e1e1e;  
                  color: #cccccc; 
                }
                .diff_header {
                  background-color: #2d2d2d; 
                  color: #6c1c0b;
                  font-weight: bold;
                }
                .diff_next {
                  background-color: #333333;
                  color: #6c1c0b;
                }
                .diff_chg {
                  background-color: #5e4d17; 
                  color: #6c1c0b;
                  font-weight: bold;
                }
                .diff_add {
                  background-color: #145228; 
                  color: #6c1c0b; 
                  font-weight: bold; 
                }
                .diff_sub {
                  background-color: #8b2424; 
                  color: #6c1c0b;
                  font-weight: bold; 
                }
                table.diff, .diff_header, .diff_next, td, th {
                  border: 1px solid #555;
                }
                .diff_linenos {
                  background-color: #252526;
                  color: #aaaaaa;
                }
                </style>
                """
                st.components.v1.html(
                    custom_css + html_diff, height=800, scrolling=True
                )
            else:
                st.success("✅ No differences found among common or mapped files.")
        else:
            st.info("Please select both sides (Branch or Tag).")
else:
    st.info("Please clone the repository or provide a valid URL.")
