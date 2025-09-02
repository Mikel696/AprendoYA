import os
import re

def build_documentation(template_path, output_path):
    # Read the content of the template file
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find placeholders like {{FILENAME.txt}}
    # This regex captures the filename including the .txt extension
    placeholders = re.findall(r'\{\{([a-zA-Z0-9_.-]+\.txt)\}\}', content)

    # Construct the absolute path to the Base64_Output directory
    # Assuming build_docs.py is in the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    base64_output_dir = os.path.join(project_root, 'Documentacion', 'Base64_Output')

    for placeholder_filename in placeholders:
        base64_file_path = os.path.join(base64_output_dir, placeholder_filename)
        try:
            with open(base64_file_path, 'r', encoding='utf-8') as f:
                image_data = f.read()
            # Replace the placeholder with the actual image data
            content = content.replace(f'{{{{{placeholder_filename}}}}}', image_data)
        except FileNotFoundError:
            print(f"Warning: Base64 file not found for {base64_file_path}. Placeholder will remain.")
        except Exception as e:
            print(f"Error reading {base64_file_path}: {e}")

    # Write the modified content to the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Documentation built successfully: {output_path}")

if __name__ == "__main__":
    # Define paths relative to the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    template_path = os.path.join(project_root, 'Documentacion', 'template_documentacion.html')
    output_path = os.path.join(project_root, 'Documentacion', 'documentacion_tecnica.html')

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Call the function to build the documentation
    build_documentation(template_path, output_path)
