#!/usr/bin/env python3
import os
import argparse
from subprocess import Popen, PIPE, run

S3CMD = "s3cmd"
STORAGEBOX = ""

tool_description = """
A tool to backup an S3 server to a hetzner storage box
"""

def run_s3cmd(args):
    process = Popen([S3CMD] + args, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("s3cmd failed with exit code %d: %s" % (exit_code, err))
    return output, err

def storagebox_mkdir(path):
    """
    Create a directory on the storage box
    """
    completion = run(["ssh", "-o", "StrictHostKeyChecking=no", "-p23", STORAGEBOX, "mkdir", "-p", path], stdout=PIPE)
    if completion.returncode != 0:
        raise RuntimeError("ssh failed with exit code %d" % (completion.returncode))

def storagebox_cp(file_name, temp_dir, dest_dir):
    """
    Copy a file from local disk to storage box
    """
    print("Copying %s to storage box" % file_name)
    completion = run(["scp", "-o", "StrictHostKeyChecking=no", "-P23", f"{temp_dir}/{file_name}", f"{STORAGEBOX}:{dest_dir}/{file_name}"], stdout=PIPE)
    if completion.returncode != 0:
        raise RuntimeError("scp failed with exit code %d" % (completion.returncode))


def s3_listall():
    """
    List all files in all buckets
    Returns:
        list of files without leading s3://. Dirs are not listed
    """
    output, _ = run_s3cmd(["la"])

    files = []
    for line in output.decode("utf-8").splitlines():
        elems = line.split("s3://")
        if len(elems) < 2:
            continue
        file_name = elems[1]
        if "DIR" in elems[0]:
            continue
        files.append(file_name)
    return files

def s3_to_storage_box_copy_file(file_name, temp_dir, dest_dir):
    print("Copying %s" % file_name)

    tries = 0 
    try:
        while True:
            try:
                print("try %d" % tries)
                run_s3cmd(["get", f"s3://{file_name}", temp_dir])
                print("s3cmd ok")
                storagebox_mkdir(os.path.dirname(f"{dest_dir}/{file_name}"))
                print("mkdir ok")
                storagebox_cp(file_name, temp_dir, dest_dir)
                print("cp ok")
                break
            except Exception as e:
                print("Error: %s, retrying" % e)
                tries += 1
                if tries > 5:
                    raise RuntimeError("Too many retries")

    finally:
        os.remove(f"{temp_dir}/{file_name}")


def s3_to_storage_box(files, temp_dir, dest_dir):
    """
    Copy files from s3 to local disk and then to storage box.
    """
    for file_name in files:
        s3_to_storage_box_copy_file(file_name, temp_dir, dest_dir)


def command_line_args_parsing():
    parser = argparse.ArgumentParser(description=tool_description)
    parser.add_argument(
        "storage_box", help="storage box user and hostname (e.g. u316870@u316870.your-storagebox.de)"
    )
    parser.add_argument(
        "dest_dir", help="root directory to write backup to on storage box"
    )
    parser.add_argument(
        "temp_dir", help="temporary directory for local storage"
    )
    return parser.parse_args()

def main():
    args = command_line_args_parsing()

    global STORAGEBOX
    STORAGEBOX = args.storage_box

    print("Starting backup")
    files = s3_listall()
    s3_to_storage_box(files, args.temp_dir, args.dest_dir)

if __name__ == "__main__":
    main()
