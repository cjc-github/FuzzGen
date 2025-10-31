import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,QMessageBox,QFileDialog,QLabel,QLineEdit
from PyQt5.QtGui import QFont, QColor, QPalette, QIntValidator
from PyQt5.QtCore import Qt, pyqtSignal
import json
import random
import os

def bytearray2str(target_str):
    if type(target_str) == type('123'):
        return target_str
    else:
        return target_str.decode('utf-8',errors='ignore')

def load_data(file_name):
    with open(file_name,'rb') as f:
        all_data_dict = json.load(f)
    return all_data_dict

def get_different(all_data_dict):
    return_dict = {}
    for question in all_data_dict:
        if "result" in all_data_dict[question]['codeqwen'] and "result" in all_data_dict[question]['content']:
            if all_data_dict[question]['codeqwen']['result'] != all_data_dict[question]['content']['result']:
                return_dict[question] = all_data_dict[question]
        else:
            return_dict[question] = all_data_dict[question]
    return return_dict


class ReadOnlyTextEdit(QTextEdit):
    clicked = pyqtSignal(str)  # 定义一个信号，传递标识符

    def __init__(self, identifier, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)  # 设置为只读模式
        self.identifier = identifier  # 添加标识符
        self.original_palette = self.palette() 
    def set_background_color(self, color):
        palette = self.palette()
        palette.setColor(QPalette.Base, color)
        self.setPalette(palette)
    def restore_background_color(self):
        self.setPalette(self.original_palette)
    def mousePressEvent(self, event):
        # 处理鼠标点击事件
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.identifier)  # 发出信号，传递标识符
        super().mousePressEvent(event)
usage = """
使用方法：
1. 点击“加载”按钮，选择待加载的文件。加载文件后，如果是从之前中断的位置重新开始，则只需要在“跳转”左边编辑栏中输入上一次保存时的位置（整数值），然后点击“跳转”，即可从上一次中断的地方开始。
2. 界面上方是问题，下方两个界面分别是两个模型的回答，选择你认为合适的回答，点击该回答即可。
3. 如果你觉得两个回答都正确，或者两个回答都不好，或者你不确定哪个回答更好，可以点击“下一步”按钮跳过该问题。
4. 如果发现刚刚点击错误或者前面的点击不正确，可以通过点击“上一步”或者“下一步”按钮实现问答对的前进或者后退，其中被点击选择过的回答的背景框会变绿。此时你可以直接点击你认为正确的回答，如果你认为刚刚两个回答都不需要选择，点击“清除”按钮，此时变绿的回答背景框会恢复为原来的背景颜色。
5. 全部回答完毕，或者中途想要保存，点击“保存”按钮，即可保存。保存时，文件尾会自动出现“_curCountXXX.json”，这部分最好不要删除。在前面加上文件名。
6. 单次执行程序后，再次点击“保存”按钮，不会出现选择框，会在你保存的地方继续保存。
7. 选择回答的时候，标题栏会显示回答的具体进度。
"""
choose_hint = """
选择回答的主要原则：
1. 对于json类回答，主要看value的回答是否正确。
2. 对于非json类回答，如果问题中带有回答结构要求，首先选择回答更合理的那一个，若两个回答都相对合理，那么选择输出格式更符合要求的结构的那一个。
3. 对于生成类的回答，选择目标代码被调用过程更具体且正确的。
"""
class CodeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        # 相关数据
        self.edit_click_staus = None
        self.candi_data_list = []
        self.current_count = -1
        # 0 代表左边，1 代表右边
        self.selected_dict = {}
        self.save_file_path = ""


        # 设置窗口标题
        self.setWindowTitle("训练数据选择器")

        # 创建顶部的 QTextEdit 控件
        self.top_text_edit = ReadOnlyTextEdit("top",self)
        font = QFont("Courier New", 12)
        self.top_text_edit.setFont(font)
        
        self.top_text_edit.setPlainText(usage)

        # 创建两个并排的 QTextEdit 控件
        self.bottom_left_text_edit = ReadOnlyTextEdit("left",self)
        self.bottom_left_text_edit.setFont(font)
        self.bottom_left_text_edit.setPlainText(choose_hint)

        self.bottom_right_text_edit = ReadOnlyTextEdit("right",self)
        self.bottom_right_text_edit.setFont(font)
        self.bottom_right_text_edit.setPlainText(choose_hint)

        self.bottom_left_text_edit.clicked.connect(self.on_bottom_left_text_edit_click)
        self.bottom_right_text_edit.clicked.connect(self.on_bottom_right_text_edit_click)

        self.jump_text_edit = QLineEdit()
        self.jump_text_edit.setValidator(QIntValidator())
        self.jump_text_edit.setFixedWidth(30)

        # 创建两个按钮
        self.prev_button = QPushButton("上一个", self)
        self.next_button = QPushButton("下一个", self)
        self.save_button = QPushButton("保存", self)
        self.load_button = QPushButton("加载", self)
        self.jump_button = QPushButton("跳转", self)
        self.clear_button = QPushButton("清空", self)
        
        self.load_button.clicked.connect(self.on_load_click)
        self.prev_button.clicked.connect(self.on_prev_click)
        self.next_button.clicked.connect(self.on_next_click)
        self.clear_button.clicked.connect(self.on_clear_click)
        self.save_button.clicked.connect(self.on_save_click)
        self.jump_button.clicked.connect(self.on_jump_click)

        # 创建布局
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.bottom_left_text_edit)
        bottom_layout.addWidget(self.bottom_right_text_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.jump_text_edit)
        button_layout.addWidget(self.jump_button)
        button_layout.addWidget(self.save_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_text_edit)
        main_layout.addLayout(bottom_layout)
        main_layout.addLayout(button_layout)

        # 设置布局
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 设置窗口大小
        self.resize(1080, 900)
    
    def process_loaded_data(self,data_dict):
        processed_list = []
        for question in data_dict:
            tmp_dict = {}
            tmp_dict['question'] = question
            codeqwen_dict = {}
            content_dict = {}
            codeqwen_dict['model'] = "codeqwen"
            content_dict['model'] = "content"
            codeqwen_dict['answer'] = data_dict[question]['codeqwen']['answer']
            content_dict['answer'] = data_dict[question]['content']['answer']
            if "result" in data_dict[question]['codeqwen'] and "result" in data_dict[question]['content']:
                codeqwen_dict['result'] = data_dict[question]['codeqwen']['result']
                content_dict['result'] = data_dict[question]['content']['result']
            index = [0,1]
            random.shuffle(index)
            tmp_dict[index[0]] = codeqwen_dict
            tmp_dict[index[1]] = content_dict
            processed_list.append(tmp_dict)
        self.candi_data_list += processed_list

    
    def on_jump_click(self):
        if self.current_count < 0:
            return
        text_str = self.jump_text_edit.text()
        try:
            jump_num = int(text_str)
            if jump_num < 0 or jump_num > len(self.candi_data_list):
                self.jump_text_edit.setText("")
                QMessageBox.warning(self, "Error", "Please enter a valid number.")
                return
            self.current_count = jump_num - 1
            selected_dict = self.candi_data_list[self.current_count]
            question = selected_dict['question']
            self.top_text_edit.setPlainText(question)
            self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
            self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))
            self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")
        except:
            self.jump_text_edit.setText("")
            QMessageBox.warning(self, "Error", "Please enter a valid number.")
            return
    def on_load_click(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Log Files (*.log)", options=options)
        if file_name:
            try:
                all_data_dict = load_data(file_name)
                diff_data_dict = get_different(all_data_dict)
                self.process_loaded_data(diff_data_dict)
                # 首次加载，current_count = -1
                if self.current_count < 0:
                    self.current_count = 0
                selected_dict = self.candi_data_list[self.current_count]
                question = selected_dict['question']
                self.top_text_edit.setPlainText(question)
                self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
                self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))
                self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")
            except Exception as e:
                print(f"捕获到异常: {type(e).__name__}")
                print(f"异常信息: {e}")
                QMessageBox.information(self, "Error", f"{file_name} read error {e}")
    def on_clear_click(self):
        if self.current_count < 0:
            return
        if self.current_count in self.selected_dict:
            del self.selected_dict[self.current_count]
        self.bottom_left_text_edit.restore_background_color()
        self.bottom_right_text_edit.restore_background_color()
    def on_next_click(self):
        if self.current_count < 0:
            return
        self.current_count += 1
        if self.current_count >= len(self.candi_data_list):
            self.current_count -= 1
            QMessageBox.information(self, "到底了", "数据到底了，请保存或者加载新的数据")
            return 

        selected_dict = self.candi_data_list[self.current_count]
        question = selected_dict['question']
        self.top_text_edit.setPlainText(question)
        self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
        self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))
        if self.current_count in self.selected_dict:
            if self.selected_dict[self.current_count] == 0:
                self.bottom_left_text_edit.set_background_color(QColor("green"))
                self.bottom_right_text_edit.restore_background_color()
            else:
                self.bottom_right_text_edit.set_background_color(QColor("green"))
                self.bottom_left_text_edit.restore_background_color()
        else:
            self.bottom_left_text_edit.restore_background_color()
            self.bottom_right_text_edit.restore_background_color()
        self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")
    def on_prev_click(self):
        if self.current_count < 0:
            return
        self.current_count -= 1
        if self.current_count < 0:
            self.current_count = 0

        selected_dict = self.candi_data_list[self.current_count]
        question = selected_dict['question']
        self.top_text_edit.setPlainText(question)
        self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
        self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))
        if self.current_count in self.selected_dict:
            if self.selected_dict[self.current_count] == 0:
                self.bottom_left_text_edit.set_background_color(QColor("green"))
                self.bottom_right_text_edit.restore_background_color()
            else:
                self.bottom_right_text_edit.set_background_color(QColor("green"))
                self.bottom_left_text_edit.restore_background_color()
        else:
            self.bottom_left_text_edit.restore_background_color()
            self.bottom_right_text_edit.restore_background_color()
        self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")
    def on_bottom_right_text_edit_click(self):
        if self.current_count < 0:
            return
        self.bottom_right_text_edit.set_background_color(QColor("green")) 
        self.bottom_left_text_edit.restore_background_color()
        self.selected_dict[self.current_count] = 1
        
        # QMessageBox.information(self, "Selected", f"{self.candi_data_list[self.current_count][1]['model']} answer selected")
        self.current_count += 1
        if self.current_count >= len(self.candi_data_list):
            self.current_count -= 1
            QMessageBox.information(self, "到底了", "数据到底了，请保存或者加载新的数据")
            return
        selected_dict = self.candi_data_list[self.current_count]
        question = selected_dict['question']
        self.top_text_edit.setPlainText(question)
        self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
        self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))

        self.bottom_right_text_edit.restore_background_color()
        self.bottom_left_text_edit.restore_background_color()

        self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")

    def on_bottom_left_text_edit_click(self):
        if self.current_count < 0:
            return
        self.bottom_right_text_edit.restore_background_color()
        self.bottom_left_text_edit.set_background_color(QColor("green")) 
        self.selected_dict[self.current_count] = 0
        # QMessageBox.information(self, "Selected", f"{self.candi_data_list[self.current_count][0]['model']} answer selected")
        self.current_count += 1
        if self.current_count >= len(self.candi_data_list):
            self.current_count -= 1
            QMessageBox.information(self, "到底了", "数据到底了，请保存或者加载新的数据")
            return 
        selected_dict = self.candi_data_list[self.current_count]
        question = selected_dict['question']
        self.top_text_edit.setPlainText(question)
        self.bottom_left_text_edit.setPlainText(bytearray2str(selected_dict[0]['answer']))
        self.bottom_right_text_edit.setPlainText(bytearray2str(selected_dict[1]['answer']))

        self.bottom_right_text_edit.restore_background_color()
        self.bottom_left_text_edit.restore_background_color()
        self.setWindowTitle(f"训练数据选择器 {self.current_count} / {len(self.candi_data_list)}")
    def on_save_click(self):
        if self.current_count < 0:
            return
        train_data_list = []
        for selected_count in self.selected_dict:
            index = self.selected_dict[selected_count]
            selected_dict = self.candi_data_list[selected_count]
            if selected_dict[index]['model'] == "content":
                train_data_dict = {}
                train_data_dict['instruction'] = selected_dict['question']
                train_data_dict['input'] = ""
                train_data_dict['output'] = selected_dict[index]['answer']
                train_data_list.append(train_data_dict)
        if self.save_file_path:
            file_name = self.save_file_path.split("_curCount:")[0]
            self.save_file_path = f"{file_name}_curCount:{self.current_count}.json"
            with open(self.save_file_path, 'w', encoding='utf-8') as f:
                json.dump(train_data_list,f)
            QMessageBox.information(self, "File Saved", f"File saved as: {file_name}")
            return 
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", f"_curCount:{self.current_count}", "json Files (*.json)", options=options)
        self.save_file_path = file_name
        try:
            with open(self.save_file_path, 'w', encoding='utf-8') as f:
                json.dump(train_data_list,f)
                QMessageBox.information(self, "File Saved", f"File saved as: {file_name}")
        except:
            QMessageBox.warning(self, "Error", "File not saved")
            return 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CodeEditor()
    window.show()
    sys.exit(app.exec_())