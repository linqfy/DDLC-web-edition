import re
import json
import os
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QLabel,
    QCheckBox,
)


def rpy_to_json(rpy_script):
    json_data = []
    current_block = {}
    in_python_block = False
    in_menu_block = False

    def add_to_output(block):
        if block:
            json_data.append(block)
            return {}
        return block

    # Compile
    label_re = re.compile(r"label\s+(\w+):")
    scene_re = re.compile(r"scene\s+(.+)")
    show_re = re.compile(r"show\s+(.+)")
    hide_re = re.compile(r"hide\s+(.+)")
    with_re = re.compile(r"with\s+(.+)")
    play_re = re.compile(r"play\s+(music|sound)\s+(.+)")
    stop_re = re.compile(r"stop\s+(music|sound)(\s+.+)?")
    char_dialogue_re = re.compile(r'(\w+)\s+"(.+)"')
    narrator_dialogue_re = re.compile(r'"(.+)"')
    menu_item_re = re.compile(r'"(.+)":$')
    image_def_re = re.compile(r"image\s+(.+?)\s*=\s*(.+)")
    transition_re = re.compile(r"(\w+)\s+(.+)")
    var_re = re.compile(r"\$\s*(.+?)\s*=\s*(.+)")
    jump_re = re.compile(r"jump\s+(.+)")
    call_re = re.compile(r"call\s+(.+)")
    pos_attr_re = re.compile(r"(at|zorder|xpos|ypos|xanchor|yanchor)\s+(.+)")
    other_attr_re = re.compile(r"(alpha|rotate|zoom|offset)\s+(.+)")

    with open("traceback.txt", "a") as f_traceback:
        for line in rpy_script.splitlines():
            line = line.strip()
            f_traceback.write(f"Current line > {line}\n")

            # Skip comments or empty lines
            if ex.ignore_comments.isChecked() and line.startswith("#"):
                continue
            if ex.ignore_empty_lines.isChecked() and not line:
                continue

            # Python block handling
            if in_python_block:
                if line == "":
                    in_python_block = False
                else:
                    current_block["python_code"] += line + "\n"
                continue

            # Menu block handling
            if in_menu_block:
                menu_item_match = menu_item_re.match(line)
                if menu_item_match:
                    # Create a new menu item if matched
                    current_block["menu"].append(
                        {"option": menu_item_match.group(1), "actions": []}
                    )
                elif line == "":
                    in_menu_block = False
                else:
                    # Only append actions if there is at least one menu item
                    if current_block["menu"]:
                        current_block["menu"][-1]["actions"].append(line.strip())
                continue

            # Label check
            label_match = label_re.match(line)
            if label_match:
                current_block = add_to_output(current_block)
                current_block["label"] = label_match.group(1)
                continue

            # Scene change check
            scene_match = scene_re.match(line)
            if scene_match:
                current_block = add_to_output(current_block)
                current_block["newBackground"] = scene_match.group(1)
                continue

            # Show statement
            show_match = show_re.match(line)
            if show_match:
                current_block = add_to_output(current_block)
                current_block["show"] = show_match.group(1)
                continue

            # Hide statement
            hide_match = hide_re.match(line)
            if hide_match:
                current_block = add_to_output(current_block)
                current_block["hide"] = hide_match.group(1)
                continue

            # With statement
            with_match = with_re.match(line)
            if with_match:
                current_block["with"] = with_match.group(1)
                continue

            # Play music or sound
            play_match = play_re.match(line)
            if play_match:
                current_block[f"play_{play_match.group(1)}"] = play_match.group(2)
                continue

            # Stop music or sound
            stop_match = stop_re.match(line)
            if stop_match:
                current_block[f"stop_{stop_match.group(1)}"] = (
                    stop_match.group(2).strip() if stop_match.group(2) else True
                )
                continue

            # Character dialogue
            char_dialogue_match = char_dialogue_re.match(line)
            if char_dialogue_match:
                current_block = add_to_output(current_block)
                current_block["char"] = char_dialogue_match.group(1)
                current_block["content"] = char_dialogue_match.group(2)
                continue

            # Narrator dialogue
            narrator_dialogue_match = narrator_dialogue_re.match(line)
            if narrator_dialogue_match:
                current_block = add_to_output(current_block)
                current_block["content"] = narrator_dialogue_match.group(1)
                continue

            # Python block start
            if line == "python:":
                in_python_block = True
                current_block["python_code"] = ""
                continue

            # Menu block start
            if line == "menu:":
                in_menu_block = True
                current_block = add_to_output(current_block)
                current_block["menu"] = []
                continue

            # Image definition
            image_match = image_def_re.match(line)
            if image_match:
                current_block = add_to_output(current_block)
                current_block["image_def"] = {
                    "name": image_match.group(1),
                    "value": image_match.group(2),
                }
                continue

            # Transitions
            transition_match = transition_re.match(line)
            if transition_match and transition_match.group(1) in [
                "dissolve",
                "fade",
                "moveinright",
                "moveinleft",
                "moveoutright",
                "moveoutleft",
            ]:
                current_block["transition"] = {
                    "type": transition_match.group(1),
                    "duration": transition_match.group(2),
                }
                continue

            # Variables
            var_match = var_re.match(line)
            if var_match:
                current_block["variable"] = {
                    "name": var_match.group(1),
                    "value": var_match.group(2),
                }
                continue

            # Jumps
            jump_match = jump_re.match(line)
            if jump_match:
                current_block["jump"] = jump_match.group(1)
                continue

            # Calls
            call_match = call_re.match(line)
            if call_match:
                current_block["call"] = call_match.group(1)
                continue

            # Return
            if line == "return":
                current_block["return"] = True
                continue

            # Position attributes
            pos_match = pos_attr_re.match(line)
            if pos_match:
                current_block[pos_match.group(1)] = pos_match.group(2)
                continue

            # Other attributes
            attr_match = other_attr_re.match(line)
            if attr_match:
                current_block[attr_match.group(1)] = attr_match.group(2)
                continue

            f_traceback.write(f"Current block > {current_block}\n")

        # Add the last block to output
        add_to_output(current_block)
        f_traceback.write(f"Current block > {current_block}\n")

    return json_data


# save data as JSON
def save_as_json(json_data, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


# -- GUI ---


class RPYConverterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("RPY to JSON Converter")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.input_label = QLabel("Input RPY file:")
        self.input_button = QPushButton("Select File")
        self.input_button.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_button)
        layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output Folder:")
        self.output_button = QPushButton("Select Folder")
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

        self.ignore_comments = QCheckBox("Ignore comments")
        self.ignore_empty_lines = QCheckBox("Ignore empty lines")
        layout.addWidget(self.ignore_comments)
        layout.addWidget(self.ignore_empty_lines)

        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)

    def select_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Input RPY File", "", "RPY Files (*.rpy)"
        )
        if file_name:
            self.input_label.setText(f"Input RPY file: {file_name}")

    def select_output_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Output Folder", "")
        if folder_name:
            self.output_label.setText(f"Output Folder: {folder_name}")

    def convert(self):
        input_file = self.input_label.text().replace("Input RPY file: ", "")
        output_folder = self.output_label.text().replace("Output Folder: ", "")

        if not input_file or not output_folder:
            print("Please select both input file and output folder.")
            return

        input_file_name = os.path.basename(input_file)
        output_file_name = os.path.splitext(input_file_name)[0] + ".json"
        output_file_path = os.path.join(output_folder, output_file_name)

        with open(input_file, "r", encoding="utf-8") as f:
            rpy_script = f.read()

        with open("traceback.txt", "w") as f:
            f.write("")

        json_data = rpy_to_json(rpy_script)

        save_as_json(json_data, output_file_path)
        print(f"Conversion completed! JSON file saved as: {output_file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = RPYConverterGUI()
    ex.show()
    sys.exit(app.exec_())
