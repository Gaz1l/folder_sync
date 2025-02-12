import argparse
import datetime
import os 
import hashlib
import shutil
import time

def validate_path(value, path_data):
    """
    Validates the path provided through the command line for the source and replica folders, and the log file. 
    If the replica folder does not exist, it will be created automatically.
    If the log file does not exist, it will be created automatically.

    Args:
        value (str): Path value provided through the command line.
        path_data (str): Data to be displayed on the error message - source, replica or log.

    Returns:
        str: Validated path value provided through the command line.
    
    Raises:
        argparse.ArgumentTypeError: If the input is a number or the path does not exist.
    """   
    # Check if input is a number
    if value.isdigit():
        raise argparse.ArgumentTypeError(f"Invalid input: '{value}' is a number, but expected a {path_data} path.")
    # Check if path exists
    if not os.path.exists(value):
        if path_data == "replica":
            # Create the replica folder
            try:
                os.makedirs(value)  
                print(f"Replica folder '{value}' did not exist. It has been created.")
            except Exception as e:
                raise argparse.ArgumentTypeError(f"Failed to create replica folder '{value}': {e}")
        elif path_data == "log" and not os.path.exists(value):
            # Create an empty log file
            try:
                with open(value, "w") as log_file:  
                    pass
                print(f"Log file '{value}' did not exist. It has been created.")
            except Exception as e:
                raise argparse.ArgumentTypeError(f"Failed to create log file '{value}': {e}")
        else:
            raise argparse.ArgumentTypeError(f"Invalid input: '{value}' is not a valid {path_data} path.")
    
    return value

def validate_path_type(path_data):
    """
    Wrapper function to include path data - source, replica or log.

    Args:
        path_data (str): Path data type ('source', 'replica' or 'log').

    Returns:
        function: Lambda function that validates the path.
    """      
    return lambda value: validate_path(value, path_data)

def calculate_md5(file_path, log_file):
    """
    Calculate the MD5 checksum of a file to detect changes.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: MD5 hash of the file.
    """
    file_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        log_operation(f"Failed to read file '{file_path}': {e}", log_file)
        return None

def get_path_data(path):
    """
    Retrieves files and directories within a specified path.

    Args:
        path (str): The directory path to analyze.

    Returns:
        dict: A dictionary containing two sets - 'files' and 'dirs'.
    """
    files = {item for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))}
    dirs = {item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item))}

    return {'files': files, 'dirs': dirs}

def sync_folders(source_path, replica_path, log_file):
    """
    Synchronizes the contents of the source folder with the replica folder.

    Args:
        source_path (str): Path to the source folder.
        replica_path (str): Path to the replica folder.
        log_file (str): Path to the log file.
    """
    # Create a dictionary containing files and directories for both source and replica
    folder_data = {
        'source': get_path_data(source_path),
        'replica': get_path_data(replica_path)
    }

    sync_files(source_path, replica_path, folder_data['source']['files'], folder_data['replica']['files'], log_file)
    sync_directories(source_path, replica_path, folder_data['source']['dirs'], folder_data['replica']['dirs'], log_file)

def file_needs_update(source_file, replica_file, log_file):
    """Checks if a file in the replica needs to be updated."""
    try:
        if not os.path.exists(replica_file):
            return True
        if os.path.getsize(source_file) != os.path.getsize(replica_file):
            return True
        if os.path.getmtime(source_file) != os.path.getmtime(replica_file):
            return True
        return calculate_md5(source_file, log_file) != calculate_md5(replica_file, log_file)
    except Exception as e:
        log_operation(f"Error comparing files '{source_file}' and '{replica_file}: {e}", log_file)
        return True

def sync_files(source_path, replica_path, source_files, replica_files, log_file):
    """
    Synchronizes files between source and replica.

    Args:
        source_path (str): Path to the source folder.
        replica_path (str): Path to the replica folder.
        source_files (set): Set of filenames in the source folder.
        replica_files (set): Set of filenames in the replica folder.
        log_file (str): Path to the log file.
    """
    for file_name in source_files:
        source_file_path = os.path.join(source_path, file_name)
        replica_file_path = os.path.join(replica_path, file_name)
        # Copy new or updated files
        if file_needs_update(source_file_path, replica_file_path, log_file):
            try:
                shutil.copy2(source_file_path, replica_file_path)
                log_operation(f"File '{file_name}' copied to replica.", log_file)
            except Exception as e:
                log_operation(f"Failed to copy file '{file_name}': {e}", log_file)
    # Delete files in replica that do not exist in source
    remove_item_from_replica(replica_path, replica_files - source_files, log_file, is_file=True)

def sync_directories(source_path, replica_path, source_dirs, replica_dirs, log_file):
    """
    Synchronizes directories between source and replica.

    Args:
        source_path (str): Path to the source folder.
        replica_path (str): Path to the replica folder.
        source_dirs (set): Set of directory names in the source folder.
        replica_dirs (set): Set of directory names in the replica folder.
        log_file (str): Path to the log file.
    """
    for dir_name in source_dirs:
        source_dir_path = os.path.join(source_path, dir_name)
        replica_dir_path = os.path.join(replica_path, dir_name)
        # Copy new directories
        if dir_name not in replica_dirs:
            try:
                shutil.copytree(source_dir_path, replica_dir_path)
                log_operation(f"Directory '{dir_name}' copied to replica.", log_file)
            except Exception as e:
                log_operation(f"Failed to copy directory '{dir_name}': {e}", log_file)
        else:
            # Recursively sync existing directories
            sync_folders(source_dir_path, replica_dir_path, log_file)

    # Remove directories that no longer exist in source
    remove_item_from_replica(replica_path, replica_dirs - source_dirs, log_file, is_file=False)

def remove_item_from_replica(replica_path, items_to_delete, log_file, is_file):
    """
    Removes files or directories from the replica folder.

    Args:
        replica_path (str): Path to the replica folder.
        items (set): Set of items (files or directories) to remove.
        is_file (bool): Flag indicating whether the items are files (True) or directories (False).
        log_file (str): Path to the log file.
    """
    for item in items_to_delete:
        replica_item_path = os.path.join(replica_path, item)
        if is_file:
            try:
                os.remove(replica_item_path)
                log_operation(f"File '{item}' deleted from replica.", log_file)
            except Exception as e: 
                log_operation(f"Failed to delete file '{item}': {e}", log_file)
        else:
            try:
                shutil.rmtree(replica_item_path)
                log_operation(f"Directory '{item}' deleted from replica.", log_file)
            except Exception as e:
                log_operation(f"Failed to delete directory '{item}': {e}", log_file)

def log_operation(message, log_file):
    """
    Logs a message to both the console and a log file.

    Args:
        message (str): The message to log.
        log_file (str): Path to the log file.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open(log_file, "a") as log:
            log.write(log_message + "\n")
    except Exception as e:
        print(f"Failed to write to log file '{log_file}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One-way folder synchronization")
    parser.add_argument("--source", type=validate_path_type("source"), required=True, help="Path to the source folder")
    parser.add_argument("--replica", type=validate_path_type("replica"), required=True, help="Path to the replica folder")
    parser.add_argument("--log", type=validate_path_type("log"), required=True, help="Path to the log file")
    parser.add_argument("--interval", type=int, required=True, help="Synchronization interval in seconds.")
    args = parser.parse_args()

    log_operation("Starting folder synchronization program.", args.log)
    log_operation(f"Source folder: {args.source}", args.log)
    log_operation(f"Replica folder: {args.replica}", args.log)
    log_operation(f"Synchronization interval: {args.interval} seconds", args.log)
    log_operation(f"Log file: {args.log}", args.log)

    next_timer = time.time() + args.interval
    while True:
        try:
            sync_folders(args.source, args.replica, args.log)
            log_operation("Synchronization complete.", args.log)
        except Exception as e:
            log_operation(f"Error during synchronization: {e}", args.log)
        
        # Avoid negative sleep
        sleep_time = max(0, next_timer - time.time())  
        time.sleep(sleep_time)
        next_timer = time.time() + args.interval
