#!/usr/bin/env python3
"""Tkinter desktop launcher for literature search workflow."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from literature_cli import LiteratureError, SearchConfig, SearchRecord, WorkflowSession


class LiteratureApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("文献检索与翻译")
        self.root.geometry("1320x860")

        self.query_var = tk.StringVar(value="thyroid cancer")
        self.max_results_var = tk.StringVar(value="1000")
        self.page_size_var = tk.StringVar(value="20")
        self.target_lang_var = tk.StringVar(value="zh-CN")
        self.fetch_more_var = tk.StringVar(value="20")
        self.status_var = tk.StringVar(value="准备就绪")
        self.page_var = tk.StringVar(value="页码: 0/0")
        self.query_info_var = tk.StringVar(value="原始关键词: - | 实际检索词: -")

        self.page = 1
        self.session = self._build_session()
        self.records_on_page: list[SearchRecord] = []
        self.busy = False

        self._build_layout()
        self._set_status("准备就绪")

    def _build_session(self) -> WorkflowSession:
        max_results = None if self.max_results_var.get().strip().lower() == "all" else int(self.max_results_var.get().strip())
        config = SearchConfig(
            max_results=max_results,
            page_size=int(self.page_size_var.get().strip()),
            language_target=self.target_lang_var.get().strip() or "zh-CN",
        )
        return WorkflowSession(config)

    def _build_layout(self) -> None:
        root_frame = ttk.Frame(self.root, padding=12)
        root_frame.pack(fill=tk.BOTH, expand=True)

        controls = ttk.LabelFrame(root_frame, text="检索控制", padding=10)
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="关键词").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.query_var, width=34).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Label(controls, text="max_results").grid(row=0, column=2, sticky="w")
        ttk.Entry(controls, textvariable=self.max_results_var, width=12).grid(row=0, column=3, padx=6)
        ttk.Label(controls, text="page_size").grid(row=0, column=4, sticky="w")
        ttk.Entry(controls, textvariable=self.page_size_var, width=10).grid(row=0, column=5, padx=6)
        ttk.Label(controls, text="翻译目标").grid(row=0, column=6, sticky="w")
        ttk.Entry(controls, textvariable=self.target_lang_var, width=12).grid(row=0, column=7, padx=6)

        self.search_button = ttk.Button(controls, text="检索", command=self.search)
        self.search_button.grid(row=1, column=0, pady=8, sticky="ew")
        self.load_cache_button = ttk.Button(controls, text="加载缓存", command=self.load_cache)
        self.load_cache_button.grid(row=1, column=1, pady=8, sticky="ew")
        ttk.Label(controls, text="继续抓取").grid(row=1, column=2, sticky="e")
        ttk.Entry(controls, textvariable=self.fetch_more_var, width=12).grid(row=1, column=3, padx=6)
        self.fetch_more_button = ttk.Button(controls, text="抓取更多", command=self.fetch_more)
        self.fetch_more_button.grid(row=1, column=4, pady=8, sticky="ew")
        self.fetch_all_button = ttk.Button(controls, text="抓取全部", command=self.fetch_all)
        self.fetch_all_button.grid(row=1, column=5, pady=8, sticky="ew")
        self.download_button = ttk.Button(controls, text="下载选中项", command=self.download_selected)
        self.download_button.grid(row=1, column=6, pady=8, sticky="ew")
        self.translate_button = ttk.Button(controls, text="翻译选中项", command=self.translate_selected)
        self.translate_button.grid(row=1, column=7, pady=8, sticky="ew")

        for index in range(8):
            controls.columnconfigure(index, weight=1 if index in {1, 7} else 0)

        nav = ttk.Frame(root_frame, padding=(0, 10))
        nav.pack(fill=tk.X)
        self.prev_button = ttk.Button(nav, text="上一页", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT)
        self.next_button = ttk.Button(nav, text="下一页", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=8)
        ttk.Label(nav, textvariable=self.page_var).pack(side=tk.LEFT, padx=12)
        ttk.Label(nav, textvariable=self.query_info_var).pack(side=tk.LEFT, padx=12)
        ttk.Label(nav, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        content = ttk.Panedwindow(root_frame, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content, padding=(0, 0, 8, 0))
        right = ttk.Frame(content)
        content.add(left, weight=3)
        content.add(right, weight=2)

        columns = ("index", "year", "source", "pmid", "title")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("index", text="序号")
        self.tree.heading("year", text="年份")
        self.tree.heading("source", text="来源")
        self.tree.heading("pmid", text="PMID")
        self.tree.heading("title", text="标题")
        self.tree.column("index", width=60, anchor="center")
        self.tree.column("year", width=70, anchor="center")
        self.tree.column("source", width=250)
        self.tree.column("pmid", width=100, anchor="center")
        self.tree.column("title", width=540)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tree_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        ttk.Label(right, text="摘要与详情").pack(anchor="w")
        self.detail_text = tk.Text(right, wrap="word", font=("Menlo", 12))
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.configure(state=tk.DISABLED)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for widget in [
            self.search_button,
            self.load_cache_button,
            self.fetch_more_button,
            self.fetch_all_button,
            self.download_button,
            self.translate_button,
            self.prev_button,
            self.next_button,
        ]:
            widget.configure(state=state)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _run_task(self, action, success_message: str | None = None) -> None:
        if self.busy:
            return

        def worker() -> None:
            try:
                result = action()
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: self._handle_error(exc))
                return
            self.root.after(0, lambda: self._finish_task(result, success_message))

        self._set_busy(True)
        threading.Thread(target=worker, daemon=True).start()

    def _handle_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_status(f"失败: {exc}")
        messagebox.showerror("操作失败", str(exc))

    def _finish_task(self, result, success_message: str | None) -> None:
        self._set_busy(False)
        if isinstance(result, list):
            self.page = 1
            self.refresh_results()
        elif isinstance(result, Path):
            self._set_status(str(result))
            messagebox.showinfo("完成", str(result))
        if success_message:
            self._set_status(success_message)

    def _rebuild_session(self, keep_state: bool = False) -> None:
        old_session = self.session
        self.session = self._build_session()
        if keep_state:
            self.session.query = old_session.query
            self.session.total_count = old_session.total_count
            self.session.results = old_session.results
            self.session.selected_indexes = old_session.selected_indexes
            self.session.last_output_dir = old_session.last_output_dir
            self.session.fetch_limit = old_session.fetch_limit
            self.session.cache_path = old_session.cache_path

    def refresh_results(self) -> None:
        self._sync_selected_from_ui()
        self.tree.delete(*self.tree.get_children())
        if not self.session.results:
            self.page_var.set("页码: 0/0")
            self.query_info_var.set("原始关键词: - | 实际检索词: -")
            self._write_detail("")
            self._set_status("当前没有结果")
            return

        total_pages = self.session.total_pages()
        self.page = max(1, min(self.page, total_pages))
        start = (self.page - 1) * self.session.config.page_size
        end = min(start + self.session.config.page_size, len(self.session.results))
        self.records_on_page = self.session.results[start:end]
        for record in self.records_on_page:
            self.tree.insert(
                "",
                tk.END,
                iid=str(record.index),
                values=(record.index, record.year, record.source, record.pmid, record.title),
            )
        for index in self.session.selected_indexes:
            iid = str(index)
            if self.tree.exists(iid):
                self.tree.selection_add(iid)
        self.page_var.set(f"页码: {self.page}/{total_pages}")
        self.query_info_var.set(
            f"原始关键词: {self.session.query or '-'} | 实际检索词: {self.session.search_query or '-'}"
        )
        self._set_status(self.session.status_line())
        if self.records_on_page:
            self._show_record(self.records_on_page[0])

    def _write_detail(self, text: str) -> None:
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state=tk.DISABLED)

    def _show_record(self, record: SearchRecord) -> None:
        text = (
            f"序号: {record.index}\n"
            f"标题: {record.title}\n"
            f"年份: {record.year}\n"
            f"来源: {record.source}\n"
            f"PMID: {record.pmid}\n"
            f"DOI: {record.doi or 'N/A'}\n"
            f"链接: {record.article_url or 'N/A'}\n"
            f"全文链接: {record.full_text_url or 'N/A'}\n"
            f"作者: {'; '.join(record.authors) if record.authors else 'N/A'}\n\n"
            f"摘要:\n{record.abstract or 'No abstract available.'}"
        )
        self._write_detail(text)

    def on_select(self, _event=None) -> None:
        self._sync_selected_from_ui()
        selection = self.tree.selection()
        if not selection:
            return
        selected_index = int(selection[0])
        record = next((item for item in self.session.results if item.index == selected_index), None)
        if record:
            self._show_record(record)

    def _sync_selected_from_ui(self) -> None:
        selected = sorted(int(item) for item in self.tree.selection())
        if selected:
            merged = set(self.session.selected_indexes)
            merged.update(selected)
            self.session.selected_indexes = sorted(merged)
            self.session.save_cache()

    def search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("缺少关键词", "请输入关键词")
            return

        def action():
            self._rebuild_session()
            return self.session.run_search(query)

        self._run_task(action, "检索完成")

    def load_cache(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("缺少关键词", "请输入关键词")
            return

        def action():
            self._rebuild_session()
            return self.session.load_cache(query)

        self._run_task(action, "缓存加载完成")

    def fetch_more(self) -> None:
        def action():
            self._rebuild_session(keep_state=True)
            return self.session.fetch_more_results(additional_count=int(self.fetch_more_var.get().strip() or "20"))

        self._run_task(action, "追加抓取完成")

    def fetch_all(self) -> None:
        if not messagebox.askyesno("确认", "抓取全部结果可能很慢，是否继续？"):
            return

        def action():
            self._rebuild_session(keep_state=True)
            return self.session.fetch_more_results(fetch_all=True)

        self._run_task(action, "已抓取全部可用结果")

    def download_selected(self) -> None:
        self._sync_selected_from_ui()

        def action():
            self._rebuild_session(keep_state=True)
            return self.session.download_selected()

        self._run_task(action, "下载完成")

    def translate_selected(self) -> None:
        self._sync_selected_from_ui()

        def action():
            self._rebuild_session(keep_state=True)
            return self.session.translate_selected()

        self._run_task(action, "翻译完成")

    def prev_page(self) -> None:
        if self.page > 1:
            self.page -= 1
            self.refresh_results()

    def next_page(self) -> None:
        if self.page < self.session.total_pages():
            self.page += 1
            self.refresh_results()


def main() -> int:
    root = tk.Tk()
    app = LiteratureApp(root)
    app.refresh_results()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
