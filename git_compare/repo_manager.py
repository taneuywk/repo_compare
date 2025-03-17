import os
import shutil
import git
import re
import streamlit as st

def remove_dir(path: str):
    """ลบโฟลเดอร์ (recursive)"""
    if os.path.exists(path):
        shutil.rmtree(path)

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
    branches = [b.name for b in repo.remotes.origin.refs]
    tags = [str(t) for t in repo.tags]
    return branches, tags

@st.cache_data
def list_files_in_ref(repo_dir: str, ref: str):
    """ดึงรายชื่อไฟล์ใน Branch หรือ Tag (เรียก 'ref')"""
    repo = git.Repo(repo_dir)
    file_list = repo.git.ls_tree('-r', '--name-only', ref).split("\n")
    return set(file_list)

@st.cache_data
def get_file_content(repo_dir: str, ref: str, file_path: str) -> str:
    """ดึงเนื้อหาไฟล์จาก ref (Branch/Tag)"""
    repo = git.Repo(repo_dir)
    try:
        return repo.git.show(f"{ref}:{file_path}")
    except git.exc.GitCommandError:
        return ""

def regex_file_mapping(files_list: set, pattern: str, replacement: str) -> dict:
    """
    ใช้ Regex เพื่อตรวจสอบชื่อไฟล์ใน files_list
    แล้วแทนที่ด้วย 'replacement' ตาม pattern ที่กำหนด
    คืนค่าเป็น dict สำหรับนำไปอัปเดตใน file_mapping
    เช่น { original_name: new_name, ... }
    """
    mapping = {}
    for filename in files_list:
        new_filename = re.sub(pattern, replacement, filename)
        if new_filename != filename:
            mapping[filename] = new_filename
    return mapping
