import os
import shutil
import sys
import subprocess 
COOKIECUTTER = "{{cookiecutter.project_name}}"
PROJECT_NAME = "cookiecutter_fastapi"
def collect_files(cwd:str):
    cwd = "/home/cyclone/workspace/cookiecutterfastapi"
    result = subprocess.run(
                ['git', "ls-files"],
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd,
            )
    files = result.stdout.strip().split('\n')
    return files


def copy_file(input, ouput):
    data = []
    print(input)
    print(ouput)
    os.makedirs(os.path.dirname(ouput), exist_ok=True)

    if "statics" in input:
        shutil.copyfile(input, ouput)
        return
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


def copy_dir(input_dir, output_dir=COOKIECUTTER):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    files = collect_files(input_dir)
    for file in files:
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(COOKIECUTTER, file.replace(PROJECT_NAME, COOKIECUTTER))
        copy_file(input_file, output_file)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        copy_dir(sys.argv[1])
    elif len(sys.argv) == 3:
        copy_dir(sys.argv[1], sys.argv[2])
    else:
        copy_dir()
