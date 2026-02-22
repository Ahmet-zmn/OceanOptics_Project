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

### Prerequisites
- Windows 10/11
- Python 3.10+ (for building from source)

### Portable Use
This application is designed to be portable. Simply download the latest release and run `USB4000_Spektrometre.exe`.

### From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/eemah/OceanOptics_Project.git
   ```
2. Run `kurulum.bat` to set up the environment and dependencies.
3. Launch the application:
   ```bash
   python usb4000_gui.py
   ```

## Building the Executable
To create a standalone EXE:
1. Ensure `cx_Freeze` and `Inno Setup` are installed.
2. Run `exe_yap.bat`.
3. The resulting setup file will be in the `dist` folder.

## Authors
- **eemah** - [GitHub](https://github.com/eemah)

## License
This project is licensed under the MIT License - see the LICENSE file for details.
