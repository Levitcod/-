import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLineEdit, QToolBar,
    QAction, QVBoxLayout, QWidget, QFileDialog, QTextBrowser,
    QMessageBox, QInputDialog, QListWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import QUrl, QSettings, Qt, QStandardPaths


class OrlandaBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orlanda Browse")
        self.resize(1200, 800)

        self.settings = QSettings("OrlandaBrowse", "Data")
        self.history = self.settings.value("history", [])
        self.bookmarks = self.settings.value("bookmarks", [])
        self.downloads = []

        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.handle_download)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        # Навигация
        back_btn = QAction("⬅️", self)
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)

        forward_btn = QAction("➡️", self)
        forward_btn.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_btn)

        reload_btn = QAction("🔄", self)
        reload_btn.triggered.connect(self.reload_page)
        nav_bar.addAction(reload_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # Действия — ВОТ ЗДЕСЬ ИСПРАВЛЕНО:
        new_tab_btn = QAction("➕", self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())  # ← лямбда!
        nav_bar.addAction(new_tab_btn)

        open_file_btn = QAction("📂", self)
        open_file_btn.triggered.connect(self.open_file)
        nav_bar.addAction(open_file_btn)

        bookmark_btn = QAction("⭐", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        nav_bar.addAction(bookmark_btn)

        bookmarks_btn = QAction("📚", self)
        bookmarks_btn.triggered.connect(self.show_bookmarks)
        nav_bar.addAction(bookmarks_btn)

        history_btn = QAction("🕒", self)
        history_btn.triggered.connect(self.show_history)
        nav_bar.addAction(history_btn)

        source_btn = QAction("</>", self)
        source_btn.triggered.connect(self.view_source)
        nav_bar.addAction(source_btn)

        save_btn = QAction("💾", self)
        save_btn.triggered.connect(self.save_page)
        nav_bar.addAction(save_btn)

        # Первая вкладка
        self.add_new_tab(QUrl("https://google.com"), "Главная")

    def add_new_tab(self, qurl=None, label="Новая"):
        if qurl is None:
            qurl = QUrl("https://google.com")
        browser = QWebEngineView()
        browser.setUrl(qurl)
        browser.urlChanged.connect(self.update_url_and_history)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def go_back(self):
        browser = self.tabs.currentWidget()
        if browser: browser.back()

    def go_forward(self):
        browser = self.tabs.currentWidget()
        if browser: browser.forward()

    def reload_page(self):
        browser = self.tabs.currentWidget()
        if browser: browser.reload()

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if text.startswith(("http://", "https://")):
            url = QUrl(text)
        elif "." in text and " " not in text:
            url = QUrl("https://" + text)
        else:
            q = text.replace(" ", "+")
            url = QUrl(f"https://www.google.com/search?q={q}")
        self.tabs.currentWidget().setUrl(url)

    def update_url_and_history(self, qurl):
        self.url_bar.setText(qurl.toString())
        url_str = qurl.toString()
        if url_str and (not self.history or self.history[-1] != url_str):
            self.history.append(url_str)
            if len(self.history) > 100:
                self.history.pop(0)
            self.settings.setValue("history", self.history)

    def open_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Web & PDF (*.html *.htm *.pdf)"
        )
        if fname:
            url = QUrl.fromLocalFile(os.path.abspath(fname))
            self.add_new_tab(url, os.path.basename(fname))

    def add_bookmark(self):
        browser = self.tabs.currentWidget()
        if browser:
            url = browser.url().toString()
            title = browser.title() or url
            if not any(b["url"] == url for b in self.bookmarks):
                self.bookmarks.append({"title": title, "url": url})
                self.settings.setValue("bookmarks", self.bookmarks)
                QMessageBox.information(self, "✅", "Закладка добавлена")

    def show_bookmarks(self):
        if not self.bookmarks:
            QMessageBox.information(self, "📚", "Нет закладок")
            return
        list_widget = QListWidget()
        for bm in self.bookmarks:
            list_widget.addItem(f"{bm['title']} — {bm['url']}")
        list_widget.itemDoubleClicked.connect(
            lambda item: self.add_new_tab(QUrl(item.text().split(" — ")[-1]), "Закладка")
        )
        i = self.tabs.addTab(list_widget, "📚 Закладки")
        self.tabs.setCurrentIndex(i)

    def show_history(self):
        if not self.history:
            QMessageBox.information(self, "🕒", "История пуста")
            return
        list_widget = QListWidget()
        for url in reversed(self.history[-50:]):
            list_widget.addItem(url)
        list_widget.itemDoubleClicked.connect(
            lambda item: self.add_new_tab(QUrl(item.text()), "История")
        )
        i = self.tabs.addTab(list_widget, "🕒 История")
        self.tabs.setCurrentIndex(i)

    def view_source(self):
        browser = self.tabs.currentWidget()
        if browser:
            def show_html(html):
                viewer = QTextBrowser()
                viewer.setPlainText(html)
                i = self.tabs.addTab(viewer, "</> Код")
                self.tabs.setCurrentIndex(i)
            browser.page().toHtml(show_html)

    def save_page(self):
        browser = self.tabs.currentWidget()
        if not browser:
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить как HTML", "", "HTML Files (*.html)")
        if not fname:
            return
        if not fname.endswith(".html"):
            fname += ".html"
        def write_html(html):
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(html)
                QMessageBox.information(self, "✅", f"Сохранено:\n{fname}")
            except Exception as e:
                QMessageBox.critical(self, "❌", f"Ошибка:\n{str(e)}")
        browser.page().toHtml(write_html)

    def handle_download(self, download):
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        suggested = download.suggestedFileName()
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", os.path.join(default_dir, suggested))
        if path:
            download.setPath(path)
            download.accept()
            self.downloads.append(path)
        else:
            download.cancel()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrlandaBrowser()
    window.show()
    sys.exit(app.exec_())