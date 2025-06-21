# Stable Diffusion Connect - Blender Addon

A Blender addon that connects to Automatic1111's Stable Diffusion WebUI API, enabling seamless AI image generation directly within Blender using img2img functionality with ControlNet support.

## Features

### Core Functionality
- **Img2Img Generation**: Render your Blender scene and use it as input for Stable Diffusion
- **ControlNet Integration**: Full ControlNet support with multiple control types
- **Camera Integration**: Generated images automatically set as camera background
- **Real-time Preview**: View sent and generated images within Blender
- **Model Management**: Automatic fetching of available models and samplers from A1111 API

### Supported ControlNet Types
- Canny Edge Detection
- Depth Maps
- Normal Maps
- OpenPose
- Scribble/Sketch
- Soft Edge Detection
- Segmentation
- MLSD (Line Detection)

### User Interface Features
- **Intuitive Panel**: Located in View3D > Sidebar > SD Connect
- **Image History**: View both sent and returned images
- **Camera Controls**: Adjust background image opacity and scale
- **Status Monitoring**: Real-time generation status with progress indicators
- **Save & Export**: Save generated images or copy to clipboard

## Installation

1. Download the `BL_A1111_Addon.py` file
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click `Install...` and select the downloaded file
4. Enable the addon by checking the box next to "Stable Diffusion Connect"
5. Configure the API address in the addon preferences

## Setup Requirements

### Automatic1111 WebUI Setup
1. Install and run [Automatic1111 Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
2. Install the [ControlNet extension](https://github.com/Mikubill/sd-webui-controlnet)
3. Launch WebUI with API enabled: `--api` flag
4. Default API address: `127.0.0.1:7860`

### Blender Requirements
- Blender 3.4.0 or higher
- Python requests library (usually included with Blender)

## Configuration

### Addon Preferences
Access via `Edit > Preferences > Add-ons > Stable Diffusion Connect`:

- **API Address**: Set your A1111 WebUI API address (default: `127.0.0.1:7860`)
- **Network Timeout**: Maximum time to wait for generation (default: 300 seconds)

### Main Settings
- **Camera**: Select which camera to use for rendering
- **Checkpoint**: Choose your Stable Diffusion model
- **Sampling Method**: Select sampler (DPM++, Euler, etc.)
- **Steps**: Number of sampling steps (default: 25)
- **CFG Scale**: Classifier-free guidance scale (default: 7.0)
- **Denoising Strength**: How much to change the input image (default: 0.75)
- **Seed**: Random seed for reproducible results (-1 for random)

### ControlNet Settings
- **Enable**: Toggle ControlNet processing
- **Control Type**: Filter available models by type
- **Preprocessor**: Choose preprocessing method
- **Model**: Select ControlNet model
- **Control Weight**: Strength of ControlNet influence (0-2)
- **Control Steps**: Start/end steps for ControlNet guidance
- **Control Mode**: Balance between prompt and ControlNet

## Usage

1. **Set up your scene** in Blender with proper lighting and composition
2. **Select a camera** from the dropdown menu
3. **Configure generation settings** (model, prompts, parameters)
4. **Enable ControlNet** if desired and select appropriate type/model
5. **Click "Generate Image"** to start the process
6. **Monitor progress** via the status indicator
7. **View results** in the Image History section

### Workflow Tips
- Use the camera's field of view controls to frame your shot
- Generated images automatically become camera backgrounds
- Adjust background opacity and scale for compositing
- Save images using the save button or copy to clipboard

## Known Issues

Based on the current version (v1.42.0), the following issues are present:

### 🐛 Copy to Clipboard Button
- **Issue**: The copy to clipboard functionality produces errors
- **Status**: Malfunctional
- **Workaround**: Use the save image function instead

### 🔍 ControlNet Model Detection
- **Issue**: Does not automatically find certain ControlNet models unless the user sets the ControlNet type to "All"
- **Status**: Partial functionality
- **Workaround**: Set ControlNet type to "All" to see all available models

### ⚠️ Generation Failures
- **Issue**: Periodically doesn't generate images for unknown reasons
- **Status**: Intermittent
- **Workaround**: Retry generation or restart the addon

### ⏱️ Timeout Functionality
- **Issue**: The timeout feature doesn't work properly and can get stuck in "generating" state forever
- **Status**: Non-functional
- **Workaround**: Go to addon preferences and click "Refresh API Data" button to reset the state

## Troubleshooting

### Connection Issues
- Ensure A1111 WebUI is running with `--api` flag
- Check that the API address in preferences is correct
- Click "Refresh API Data" to test connection
- Verify no firewall is blocking the connection

### Generation Problems
- Check console output for detailed error messages
- Ensure selected camera exists and is valid
- Verify ControlNet models are properly installed
- Try reducing image resolution for faster generation

### Performance Tips
- Enable "Low VRAM" option if running on limited GPU memory
- Reduce sampling steps for faster generation
- Use lower resolution for testing, higher for final renders

## API Endpoints Used

The addon communicates with the following A1111 API endpoints:
- `/sdapi/v1/img2img` - Main image generation
- `/sdapi/v1/sd-models` - Available Stable Diffusion models
- `/sdapi/v1/samplers` - Available sampling methods
- `/controlnet/model_list` - Available ControlNet models
- `/controlnet/module_list` - Available ControlNet preprocessors

## Version History

- **v1.42.0** - Current version with img2img, ControlNet support, and camera integration

## Contributing

This addon is open for improvements and bug fixes. When contributing:
- Test thoroughly with different A1111 setups
- Document any new features or changes
- Report bugs with detailed reproduction steps

## License

This addon is provided as-is for educational and creative purposes. Please ensure compliance with Stable Diffusion model licenses and terms of service.

---

**Note**: This addon requires an active internet connection and a running Automatic1111 WebUI instance to function properly. 