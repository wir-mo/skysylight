# SkysyLight
SkysyLight is a versatile system for integrating your Skype for Business presence status with an external LED light, allowing you to visually signal your availability to colleagues at a glance.
It is also easily extensible to suit you needs. With the easy to use serial interface there are endless possibilities as an indicator for other applications.

<img src="https://github.com/user-attachments/assets/7dceaa10-4ed0-4d24-b9cc-97878dcbd088" data-canonical-src="https://github.com/user-attachments/assets/7dceaa10-4ed0-4d24-b9cc-97878dcbd088" width="500" />
<a href="https://www.tindie.com/products/wirmo/skysylight/?ref=offsite_badges&utm_source=sellers_enwi&utm_medium=badges&utm_campaign=badge_large"><img src="https://d2ss6ovg47m0r5.cloudfront.net/badges/tindie-larges.png" alt="I sell on Tindie" width="200" height="104"></a>

## Features:
- **Real-time Presence Sync**: Sync your Skype for Business presence status with an external LED light, providing instant visual feedback to your team members.
- **Customizable LED Notifications**: Customize LED colors and patterns for different presence states such as available, busy, away, or offline.
- **Automatic Connection**: Automatically detect and connect to the LED device when plugged in, ensuring seamless integration with your workspace setup.

## Installation:
- Clone the SkysyLight repository to your local machine.
- Create a virtual environment using `python -m venv venv` and activate it with `venv\Scripts\activate` on Windows or `source venv/bin/activate` on Unix-like systems.
- Install the required Python packages using `pip install -r requirements.txt`.
- Run the main.py script to start syncing your Skype for Business presence status with the LED light.

### Building single file exe
Run `pyinstaller -F --add-binary Microsoft.Lync.Controls.dll:. --add-binary Microsoft.Lync.Model.dll:. --add-binary Microsoft.Office.Uc.dll:. --add-data gray.png:. --add-data green.png:. --add-data red.png:. --add-data yellow.png:. .\main.py` within the windows folder

## Usage:
- Connect the SkysyLight board to your computer via USB.
- Launch SkysyLight and verify that your Skype for Business presence status is being synchronized with the LED light.
- Enjoy instant visual notifications of your presence status, helping you stay productive and connected with your team.

## Contribution:
Contributions to SkysyLight are welcome! If you have ideas for improvements, bug fixes, or new features, please feel free to submit a pull request or open an issue on GitHub.

## License:
SkysyLight is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
