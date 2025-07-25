# Twitter Media Likes Downloader (v1.1)
This tool is a Python script ran in Command Prompt that uses ChromeDriver and Selenium to bulk-download all pieces of media from your Twitter likes, in the highest quality possible.

This is done by opening a ChromeDriver tab which prompts you to login to Twitter. Once you've done so (and followed the instructions), it will automatically scroll down through your likes and download every piece of media it comes across. 
Keep in mind that gifs will not be downloaded in their original file type, but rather in video form to preserve quality.

### Dependencies:
- [Python 3](https://www.python.org/downloads/)
- Selenium Extension [pip install selenium requests pillow]
- [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/)
- Either [Chrome](https://www.google.com/chrome/) or [Brave](https://brave.com/) browser

### Usage:
1. Download either the **Brave** or **Chrome** folders from the directory
2. Open *start.bat* (or *media_downloader.py*)
3. Follow the instructions!

I really made this only for myself as I constantly like tweets with images/videos, and I'd like to keep them preserved on my computer - but I figured maybe there's someone out there who'll use this. If you're that person, I hope this serves you well!
