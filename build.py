import os
import shutil
import sys

COOKIECUTTER = "{{cookiecutter.project_name}}"


def copy_file(input, ouput):
    data = []
    print(input)
    with open(input, "r", encoding="utf-8") as f:
        for line in f.readlines():

            if "0.0.0" in line and "version" in line.lower():
                line = line.replace("0.0.0", "{{cookiecutter.version}}")
            elif "email@email.com" in line:
                line = line.replace("email@email.com", "{{cookiecutter.email}}")
            elif "cookiecutter_fastapi" in line:
                line = line.replace("cookiecutter_fastapi", COOKIECUTTER)
            data.append(line)

    with open(ouput, "w", encoding="utf-8") as f:
        f.writelines(data)


def copy_dir(input="cookiecutter_fastapi", output=COOKIECUTTER):
    if os.path.exists(output):
        shutil.rmtree(output)
    os.mkdir(output)

    files = os.listdir(input)
    for file in files:
        if file in [
            "__pycache__",
            ".dev.env",
            ".prod.env",
            ".pytest_cache",
            ".ruff_cache",
            ".hypothesis",
            ".venv",
            "logs",
            ".git",
            "pdm.lock",
            ".pdm-python",
            ".coverage",
            "htmlcov",
        ]:
            continue
        input_file = os.path.join(input, file)
        if file == "cookiecutter_fastapi":
            output_file = os.path.join(output, COOKIECUTTER)
        else:
            output_file = os.path.join(output, file)

        if os.path.isfile(input_file):
            copy_file(input_file, output_file)
        elif os.path.isdir(input_file):
            if file == "statics":
                shutil.copytree(input_file, output_file)
            else:
                copy_dir(input_file, output_file)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        copy_dir(sys.argv[1])
    elif len(sys.argv) == 3:
        copy_dir(sys.argv[1], sys.argv[2])
    else:
        copy_dir()
