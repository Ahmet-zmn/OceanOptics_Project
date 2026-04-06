# Ocean Optics USB4000 Spectrometer Controller

A portable, user-friendly GUI application for controlling the Ocean Optics USB4000 spectrometer. Developed using Python, Tkinter, and the OceanDirect SDK.

## Features
- **Real-time Monitoring**: Live spectral data visualization.
- **Transmission Workflow**: Integrated dark and reference measurement steps for transmission spectroscopy.
- **Wavelength Monitor**: Track specific wavelengths with a live trend graph.
- **OriginPro Integration**: Direct export and opening of the latest measurements in OriginPro.
- **Localization**: Supports English and Turkish.
- **Driver Management**: Built-in tool for installing WinUSB drivers.

## Installation

### The Easiest Way
1. Go to the `dist` folder in this repository.
2. Download and run `OceanOptics_Controller_Setup.exe`.
3. Follow the on-screen instructions to install the application.

### From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/Ahmet-zmn/OceanOptics_Project.git
   ```
2. Install dependencies (requires Python 3.10+):
   ```bash
   pip install numpy matplotlib
   ```
3. Launch the application:
   ```bash
   python OceanOptics_Controller.py
   ```

## Authors
- **Ahmet-zmn** - [GitHub](https://github.com/Ahmet-zmn)

## License
This project is licensed under the MIT License - see the LICENSE file for details.
