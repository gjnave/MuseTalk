import os
import gradio as gr
import subprocess
import yaml

# Function to update the YAML file
def update_yaml(audio_path, video_path, config_path=r'./configs/inference/test.yaml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    if 'task_0' not in config:
        config['task_0'] = {}
    
    config['task_0']['audio_path'] = audio_path
    config['task_0']['video_path'] = video_path
    
    config.pop('audio_path', None)
    config.pop('video_path', None)
    
    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)

# Function to convert video to MP4 with 24 fps
def convert_video(video_path):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join('./results', f"{base_name}.mp4")
    command = f"ffmpeg -y -i \"{video_path}\" -r 24 \"{output_path}\""
    subprocess.run(command, shell=True)
    print(f"Converted video saved to: {output_path}")  # Debugging line
    return output_path

# Function to run the inference script
def run_inference(audio_file, video_file):
    audio_path = os.path.abspath(audio_file)
    video_path = os.path.abspath(video_file)
    
    # Check if the video is already MP4 or needs conversion
    if video_path.lower().endswith('.webm'):
        # Convert the video file to MP4
        converted_video_path = convert_video(video_path)
    else:
        converted_video_path = video_path
    
    # Update the YAML configuration with the file paths
    update_yaml(audio_path, converted_video_path)
    
    base_directory = os.path.abspath('.')
    os.chdir(base_directory)
    
    command = ['python', '-m', 'scripts.inference', '--inference_config', 'configs/inference/test.yaml']
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        output = result.stdout
    except subprocess.CalledProcessError as e:
        output = f"Error executing command: {e}\n"
        output += e.stdout if e.stdout else ""
        output += e.stderr if e.stderr else ""
    
    print("Inference Output:")
    print(output)
    
    # Determine the generated video path with video_audio naming convention
    generated_video_name = f"{os.path.splitext(os.path.basename(video_file))[0]}_{os.path.splitext(os.path.basename(audio_file))[0]}.mp4"
    generated_video_path = os.path.join('./results', generated_video_name)
    
    # Ensure the path is correct for Gradio
    gradio_video_path = generated_video_path
    
    return output, gradio_video_path

# Define the Gradio interface
audio_input = gr.Audio(label='Upload Audio File', type='filepath')
video_input = gr.Video(label='Upload Video File')

def inference_interface(audio_file, video_file):
    output, generated_video_path = run_inference(audio_file, video_file)
    return output, generated_video_path

# Custom CSS to further reduce the height of the output textbox and align it with the video input box
custom_css = """
.ace_editor.ace_autocomplete {
    height: 150px !important;
}
.gr-output {
    margin-top: 20px;
}
"""

# Launch the Gradio interface
gr.Interface(
    fn=inference_interface, 
    inputs=[audio_input, video_input], 
    outputs=[gr.Textbox(), gr.Video(format='mp4')],
    title="Inference Runner",
    description="Upload your audio and video files to run inference and view results.",
    css=custom_css
).launch()
