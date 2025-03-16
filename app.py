import streamlit as st
import os

from git_compare import repo_manager, diff_utils


# ฟังก์ชันโหลด CSS จากไฟล์
def load_custom_css(css_path: str) -> str:
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# ----- ตั้งค่าหน้าตา Streamlit ----- #
st.set_page_config(
    page_title="Git Compare - Remove Old Folder on URL Change", layout="wide"
)
st.title(
    "🔍 Git Repository Compare - Branch or Tag, Dark Theme, Folder Remove on URL Change"
)

# ========== 1) ตรวจจับ URL เปลี่ยน + ลบโฟลเดอร์เดิม + Clear cache ========== #
if "old_repo_url" not in st.session_state:
    st.session_state.old_repo_url = ""

repo_url = st.text_input("📂 Git Repository URL:", "https://github.com/ollama/ollama")
repo_dir = "./git_repo"

if repo_url != st.session_state.old_repo_url and st.session_state.old_repo_url != "":
    st.warning(
        f"Repo URL changed from {st.session_state.old_repo_url} to {repo_url}. Removing old folder & clearing cache."
    )
    repo_manager.remove_dir(repo_dir)
    st.cache_data.clear()

st.session_state.old_repo_url = repo_url

# ===== ปุ่ม Reload Cache ด้วยตัวเอง ===== #
if st.button("Reload Cache"):
    st.cache_data.clear()
    st.success("Cache cleared manually!")

# ===== ปุ่ม Clone ===== #
if st.button("Clone Repository"):
    with st.spinner("Cloning or Checking..."):
        repo_manager.clone_repo_if_not_exists(repo_url, repo_dir)
    st.success("Repository is ready!")

# ===== ถ้ามีโฟลเดอร์แล้ว => ดึง Branch/Tag ===== #
if os.path.exists(repo_dir):
    branches, tags = repo_manager.get_all_branches_and_tags(repo_dir)
    if not branches and not tags:
        st.error("No Branches or Tags found in this repository.")
    else:
        # ----- สร้าง Radio Button ฝั่งซ้าย ว่าจะเทียบ Branch / Tag ----- #
        st.subheader("Compare Side 1")
        compare_type_1 = st.radio(
            "Compare type 1", ["Branch", "Tag"], index=0, horizontal=True
        )
        ref_list_1 = branches if compare_type_1 == "Branch" else tags
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
        ref_list_2 = branches if compare_type_2 == "Branch" else tags
        side2 = (
            st.selectbox("Select side 2", ref_list_2, key="side2_select")
            if ref_list_2
            else None
        )

        if side1 and side2:
            files_side1 = repo_manager.list_files_in_ref(repo_dir, side1)
            files_side2 = repo_manager.list_files_in_ref(repo_dir, side2)

            only_in_side1 = files_side1 - files_side2
            only_in_side2 = files_side2 - files_side1
            common_files = files_side1.intersection(files_side2)

            st.subheader("📁 Folder & File Structure Differences")
            col_left, col_right = st.columns(2)
            with col_left:
                st.write(f"Files only in `{side1}`:")
                st.code(
                    "\n".join(sorted(only_in_side1)) if only_in_side1 else "— None —"
                )
            with col_right:
                st.write(f"Files only in `{side2}`:")
                st.code(
                    "\n".join(sorted(only_in_side2)) if only_in_side2 else "— None —"
                )

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
            compare_pairs = {f: f for f in common_files}
            for old_name, new_name in st.session_state.file_mapping.items():
                compare_pairs[old_name] = new_name

            # ----- Partial Diff: สรุปไฟล์ที่ต่าง ----- #
            summary_data = []
            for f1, f2 in compare_pairs.items():
                content1 = repo_manager.get_file_content(repo_dir, side1, f1)
                content2 = repo_manager.get_file_content(repo_dir, side2, f2)
                if content1 and content2 and (content1 != content2):
                    changed = diff_utils.quick_diff_lines(content1, content2)
                    if changed > 0:
                        summary_data.append(
                            {"file1": f1, "file2": f2, "changed_lines": changed}
                        )

            if summary_data:
                st.subheader("📝 Differences Summary")
                st.table(summary_data)

                pair_display_list = [
                    f"{item['file1']} => {item['file2']} (Changed {item['changed_lines']} lines)"
                    for item in summary_data
                ]
                selected_pair_str = st.selectbox(
                    "📄 Select File Pair to Compare:", pair_display_list
                )

                reverse_map = {
                    f"{item['file1']} => {item['file2']} (Changed {item['changed_lines']} lines)": (
                        item["file1"],
                        item["file2"],
                    )
                    for item in summary_data
                }

                file1, file2 = reverse_map[selected_pair_str]
                c1 = repo_manager.get_file_content(repo_dir, side1, file1)
                c2 = repo_manager.get_file_content(repo_dir, side2, file2)

                st.subheader(f"🔍 Side-by-Side Diff: {file1} => {file2}")
                html_diff = diff_utils.make_side_by_side_diff(
                    c1, c2, f"{side1}:{file1}", f"{side2}:{file2}"
                )

                # โหลด custom CSS จากไฟล์
                custom_css = load_custom_css("assets/custom.css")
                css_content = load_custom_css("assets/custom.css")
                css_tag = f"<style>{css_content}</style>"

                html_content = css_tag + html_diff
                st.components.v1.html(html_content, height=800, scrolling=True)
                # st.components.v1.html(
                #     custom_css + html_diff, height=800, scrolling=True
                # )
            else:
                st.success("✅ No differences found among common or mapped files.")
        else:
            st.info("Please select both sides (Branch or Tag).")
else:
    st.info("Please clone the repository or provide a valid URL.")
