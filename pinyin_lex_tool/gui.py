"""图形用户界面"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import threading

from .service import PinyinLexService
from .lex_reader import LexFileReader
from .models import PinyinPhrase


def get_user_lex_path() -> str:
    """获取用户微软拼音自定义短语文件路径"""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        raise RuntimeError("无法获取 APPDATA 环境变量")
    return os.path.join(appdata, "Microsoft", "InputMethod", "Chs", "ChsPinyinEUDPv1.lex")


class PhraseEditDialog(tk.Toplevel):
    """短语编辑对话框"""
    
    def __init__(self, parent, pinyin: str, index: int = 1, text: str = "", is_new: bool = False):
        super().__init__(parent)
        self.result = None
        self.is_new = is_new
        
        title = "新增短语" if is_new else "编辑短语"
        self.title(title)
        self.resizable(False, False)
        
        self._setup_ui(pinyin, index, text)
        self.center_window()
        
    def _setup_ui(self, pinyin: str, index: int, text: str):
        """设置界面"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="拼音:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pinyin_entry = ttk.Entry(main_frame, width=30)
        self.pinyin_entry.insert(0, pinyin)
        self.pinyin_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(main_frame, text="索引 (1-9):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.index_entry = ttk.Entry(main_frame, width=10)
        self.index_entry.insert(0, str(index))
        self.index_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(main_frame, text="短语内容:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(main_frame, width=40)
        self.text_entry.insert(0, text)
        self.text_entry.grid(row=2, column=1, pady=5, padx=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        self.text_entry.focus_set()
        
    def center_window(self):
        """居中窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def _on_ok(self):
        """确定按钮处理"""
        pinyin = self.pinyin_entry.get().strip()
        index_str = self.index_entry.get().strip()
        text = self.text_entry.get().strip()
        
        if not pinyin:
            messagebox.showerror("错误", "拼音不能为空")
            return
            
        if not self.service._validate_pinyin(pinyin):
            messagebox.showerror("错误", "拼音格式不正确，只能包含字母，最多 32 个字符")
            return
            
        try:
            index = int(index_str)
            if index < 1 or index > 9:
                messagebox.showerror("错误", "索引必须在 1-9 之间")
                return
        except ValueError:
            messagebox.showerror("错误", "索引必须是数字")
            return
            
        if not text:
            messagebox.showerror("错误", "短语内容不能为空")
            return
            
        if len(text) > 64:
            messagebox.showerror("错误", "短语内容不能超过 64 个字符")
            return
            
        self.result = (pinyin.lower(), index, text)
        self.destroy()

class MSPhraseToolGUI:
    """微软拼音短语管理工具 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MSPhraseTool - 微软拼音短语管理工具")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        self.service = PinyinLexService(LexFileReader())
        self.lex_path = get_user_lex_path()
        self.current_phrases = []
        
        self._setup_ui()
        self._load_phrases()
        
    def _setup_ui(self):
        """设置用户界面"""
        # 顶部搜索区域
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="拼音查询:").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        ttk.Button(search_frame, text="查询", command=self._search_phrases).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="清空", command=self._clear_search).pack(side=tk.LEFT, padx=5)
        
        # 短语列表区域
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Treeview
        columns = ("index", "pinyin", "text")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("index", text="索引")
        self.tree.heading("pinyin", text="拼音")
        self.tree.heading("text", text="短语内容")
        
        self.tree.column("index", width=60, anchor=tk.CENTER)
        self.tree.column("pinyin", width=150, anchor=tk.W)
        self.tree.column("text", width=400, anchor=tk.W)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作按钮区域
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="新增短语", command=self._add_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑", command=self._edit_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self._delete_phrase).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self._refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出", command=self._export).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="上传到云端", command=self._upload).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _load_phrases(self):
        """加载短语列表"""
        try:
            self.status_var.set("正在加载短语...")
            self.current_phrases = self.service.list_phrases(self.lex_path)
            self._refresh_tree()
            self.status_var.set(f"就绪 - 共 {len(self.current_phrases)} 条短语")
        except Exception as e:
            self.status_var.set(f"错误：{str(e)}")
            messagebox.showerror("错误", f"加载短语失败：{str(e)}")
            
    def _refresh_tree(self, filter_pinyin: str = ""):
        """刷新树形视图"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for phrase in self.current_phrases:
            if filter_pinyin and phrase.pinyin.lower() != filter_pinyin.lower():
                continue
                
            self.tree.insert("", tk.END, values=(
                phrase.index,
                phrase.pinyin,
                phrase.text
            ))
            
    def _on_search(self, event=None):
        """搜索输入处理"""
        self._search_phrases()
        
    def _search_phrases(self):
        """搜索短语"""
        pinyin = self.search_entry.get().strip()
        self._refresh_tree(pinyin)
        self.status_var.set(f"查询结果：{len([p for p in self.current_phrases if not pinyin or p.pinyin.lower() == pinyin.lower()])} 条")
        
    def _clear_search(self):
        """清空搜索"""
        self.search_entry.delete(0, tk.END)
        self._refresh_tree()
        self.status_var.set(f"就绪 - 共 {len(self.current_phrases)} 条短语")

    def _add_phrase(self):
        """新增短语"""
        dialog = PhraseEditDialog(self.root, pinyin="", index=1, text="", is_new=True)
        dialog.service = self.service
        self.root.wait_window(dialog)
        
        if dialog.result:
            pinyin, index, text = dialog.result
            try:
                self.service.update_single_phrase(self.lex_path, pinyin, index, text)
                self._load_phrases()
                messagebox.showinfo("成功", f"已新增短语：{pinyin} -> {text}")
            except Exception as e:
                messagebox.showerror("错误", f"新增失败：{str(e)}")
                
    def _edit_phrase(self):
        """编辑短语"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要编辑的短语")
            return
            
        item = self.tree.item(selected[0])
        index, pinyin, text = item["values"]
        
        dialog = PhraseEditDialog(self.root, pinyin=pinyin, index=index, text=text, is_new=False)
        dialog.service = self.service
        self.root.wait_window(dialog)
        
        if dialog.result:
            new_pinyin, new_index, new_text = dialog.result
            try:
                if new_pinyin != pinyin or new_text != text:
                    self.service.delete_single_phrase(self.lex_path, pinyin, index, text)
                self.service.update_single_phrase(self.lex_path, new_pinyin, new_index, new_text)
                self._load_phrases()
                messagebox.showinfo("成功", f"已更新短语：{new_pinyin} -> {new_text}")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败：{str(e)}")
                
    def _delete_phrase(self):
        """删除短语"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的短语")
            return
            
        item = self.tree.item(selected[0])
        index, pinyin, text = item["values"]
        
        if messagebox.askyesno("确认删除", f"确定要删除短语吗？\n拼音：{pinyin}\n索引：{index}\n内容：{text}"):
            try:
                self.service.delete_single_phrase(self.lex_path, pinyin, index, text)
                self._load_phrases()
                messagebox.showinfo("成功", "已删除短语")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{str(e)}")
                
    def _refresh(self):
        """刷新短语列表"""
        self._load_phrases()
        
    def _export(self):
        """导出短语"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile="自定义短语.csv"
        )
        
        if file_path:
            try:
                self.service.export(self.lex_path, file_path)
                messagebox.showinfo("成功", f"已导出到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def _upload(self):
        """上传到云端"""
        try:
            import subprocess
            from pathlib import Path
            
            if getattr(sys, 'frozen', False):
                script_dir = Path(__file__).parent.parent / "tool"
            else:
                script_dir = Path(__file__).parent.parent / "tool"
                
            upload_script = script_dir / "upload_to_s3.py"
            
            if not upload_script.exists():
                messagebox.showerror("错误", f"上传脚本不存在：{upload_script}")
                return
                
            def upload_thread():
                try:
                    self.status_var.set("正在上传到云端...")
                    result = subprocess.run(
                        [sys.executable, str(upload_script)],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        self.status_var.set("上传完成")
                        messagebox.showinfo("成功", "上传到云端成功！\n\n" + result.stdout)
                    else:
                        self.status_var.set("上传失败")
                        messagebox.showerror("错误", f"上传失败：\n{result.stderr}")
                except Exception as e:
                    self.status_var.set("上传出错")
                    messagebox.showerror("错误", f"上传出错：{str(e)}")
                    
            thread = threading.Thread(target=upload_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"上传功能出错：{str(e)}")
            
    def run(self):
        """运行 GUI"""
        self.root.mainloop()


def main():
    """GUI 主入口"""
    app = MSPhraseToolGUI()
    app.run()


if __name__ == "__main__":
    main()
