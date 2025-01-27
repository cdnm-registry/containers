import yaml
import re
import argparse

def process_image_string(image_str, prefix, suffix):
    # Split image into repository and tag if it contains a tag
    if ':' in image_str:
        repo, tag = image_str.rsplit(':', 1)
    else:
        repo = image_str
        tag = 'latest'

    # Replace non-alphanumeric with '-' and make lowercase
    new_repo = f"{re.sub(r'[^a-zA-Z0-9]', '-', repo).lower()}-{re.sub(r'[^a-zA-Z0-9]', '-', tag).lower()}"
    # Prepend prefix and append suffix
    new_repo = f"{prefix}-{new_repo}"
    return f"{new_repo}:{suffix}", f"{repo}:{tag}"

def find_repository_tag(data):
    """Recursively search for repository and tag in a dictionary"""
    results = []
    
    def search_dict(d):
        if not isinstance(d, dict):
            return
        
        repo = d.get('repository')
        tag = d.get('tag', 'latest')
        if repo is not None:
            results.append((repo, tag if tag else 'latest'))
        
        # Continue searching in all dictionary values
        for value in d.values():
            if isinstance(value, dict):
                search_dict(value)
    
    search_dict(data)
    return results

def process_yaml(yaml_file, output_yaml, prefix, suffix, orig_images_file, new_images_file):
    # Lists to store original and new image names
    original_images = []
    new_images = []

    def process_dict(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'image':
                    if isinstance(value, str):
                        new_image, orig_image = process_image_string(value, prefix, suffix)
                        data[key] = new_image
                        original_images.append(orig_image)
                        new_images.append(new_image)
                    elif isinstance(value, dict):
                        repo_tag_pairs = find_repository_tag(value)
                        for repo, tag in repo_tag_pairs:
                            orig_image = f"{repo}:{tag}"
                            new_image, _ = process_image_string(orig_image, prefix, suffix)
                            new_repo, new_tag = new_image.rsplit(':', 1)

                            # Find and update the specific dict containing this repository/tag
                            def update_repo_tag(d, orig_repo):
                                if d.get('repository') == orig_repo:
                                    d['repository'] = new_repo
                                    d['tag'] = new_tag
                                    return True
                                for v in d.values():
                                    if isinstance(v, dict):
                                        if update_repo_tag(v, orig_repo):
                                            continue
                                return False

                            update_repo_tag(value, repo)
                            original_images.append(orig_image)
                            new_images.append(new_image)
                elif isinstance(value, (dict, list)):
                    process_dict(value)
        elif isinstance(data, list):
            for item in data:
                process_dict(item)

    # Read YAML file
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Create a deep copy and process the YAML data
    processed_data = yaml.safe_load(yaml.dump(data))
    process_dict(processed_data)

    # Write modified YAML to new output file
    with open(output_yaml, 'w') as f:
        yaml.dump(processed_data, f, default_flow_style=False)

    # Write original images to orig-images.txt
    with open(orig_images_file, 'w') as f:
        f.write('\n'.join(original_images))

    # Write new images to new-images.txt
    with open(new_images_file, 'w') as f:
        f.write('\n'.join(new_images))

def main():
    parser = argparse.ArgumentParser(description='Process YAML file to transform image names')
    parser.add_argument('input_yaml', help='Input YAML file')
    parser.add_argument('output_yaml', help='Output YAML file')
    parser.add_argument('prefix', help='Prefix for new image names')
    parser.add_argument('suffix', help='Suffix for new image tags')
    parser.add_argument('orig_images', help='File to store original image names')
    parser.add_argument('new_images', help='File to store new image names')

    args = parser.parse_args()

    process_yaml(args.input_yaml, args.output_yaml, args.prefix, args.suffix,
                args.orig_images, args.new_images)

if __name__ == '__main__':
    main()
