# 🎬 MPV Playlist Player Pro

Professional high-performance M3U playlist player with MPV integration and modern dark UI.

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## ✨ Features

- **🚀 High Performance**: Optimized memory usage with immutable data structures and lazy evaluation
- **🎨 Modern UI**: Professional dark theme interface built with Tkinter
- **📡 Auto-Download**: Automatic playlist refresh from acestream_search
- **🔍 Smart Search**: Real-time filtering by channel name, URL, and category
- **📊 Progress Tracking**: Visual progress dialog for playlist downloads
- **🎯 Category Filtering**: Group and filter channels by metadata tags
- **⚡ Quick Playback**: Double-click or Enter to start playback instantly
- **💾 Memory Efficient**: Slot-based classes and frozen dataclasses minimize RAM usage

## 📋 Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- MPV player executable (`mpv.exe` on Windows, `mpv` on Linux/macOS)
- acestream-search package

## 🔧 Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-name>

# Install dependencies with uv
uv sync

# Run the application
uv run main.py
```

### Manual Installation

```bash
pip install acestream-search customtkinter nuitka ttkbootstrap
```

## 🎮 Usage

### Running from Source

```bash
uv run main.py
```

### First Launch

1. The application will automatically download the playlist on startup
2. Wait for the progress dialog to complete (~2100 streams)
3. Browse channels using search or category filter
4. Double-click any channel to play

### Controls

- **🔄 Refresh Playlist**: Download latest playlist from acestream_search
- **▶ Play**: Start playback of selected channel
- **⏹ Stop**: Terminate current playback
- **🔍 Search**: Filter channels by name or URL
- **📂 Category**: Filter by metadata tags

### MPV Setup

Place the MPV executable in the project root directory:

- **Windows**: `mpv.exe`
- **Linux/macOS**: `mpv` (ensure it's in PATH or local directory)

Download MPV from [mpv.io](https://mpv.io/installation/)

## 🏗️ Building Executable

### Build with Nuitka locally

```bash
uv run nuitka --onefile --windows-console-mode=disable --enable-plugin=tk-inter main.py
```

### Build Options

- `--onefile`: Create single executable file
- `--windows-console-mode=disable`: No console window (Windows GUI mode)
- `--enable-plugin=tk-inter`: Include Tkinter support
- Add `--standalone` for full dependency bundling

### Output

Compiled executable will be in `build/` directory:

- Windows: `main.exe`
- Linux: `main.bin`
- macOS: `main.app`

## 🤖 Automated Builds

GitHub Actions automatically builds executables for Windows, Linux, and macOS on every release. See [release.yml](.github/workflows/release.yml) for details.

## 📁 Project Structure

```
.
├── main.py              # Main application
├── pyproject.toml       # uv project configuration
├── playlist.m3u         # Downloaded playlist (auto-generated)
├── save_playlist.bat    # Manual playlist download script (Windows)
├── mpv.exe             # MPV player (Windows, not included)
└── README.md           # This file
```

## 🏛️ Architecture

### Classes

- **`Channel`**: Immutable dataclass with slots for minimal memory footprint
- **`M3UParser`**: High-performance parser with LRU caching and regex optimization
- **`PlaylistDownloader`**: Async download manager with progress callbacks
- **`MPVController`**: Process manager for MPV player lifecycle
- **`ProgressDialog`**: Modern progress UI with real-time updates
- **`ModernPlaylistPlayer`**: Main application with event-driven architecture

### Design Principles

- **Immutability**: Frozen dataclasses prevent accidental mutations
- **Lazy Evaluation**: Parse-on-demand with caching
- **Slot Optimization**: `__slots__` reduce memory overhead by ~40%
- **Type Safety**: Full type hints for maintainability
- **Separation of Concerns**: Each class handles single responsibility

## 🛠️ Development

### Code Style

- PEP 8 compliant
- Type hints on all functions
- Docstrings for public APIs
- Minimal loops and conditionals (functional patterns preferred)

### Performance Optimizations

- Regex pattern compilation at class level
- LRU cache for parsed playlists
- Tuple-based immutable collections
- Generator patterns for memory efficiency
- Subprocess with `DEVNULL` for silent operations

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please ensure:

- Code follows existing architecture patterns
- Type hints are included
- Memory efficiency is maintained
- UI consistency with dark theme

## 🐛 Troubleshooting

### MPV not found

Ensure `mpv.exe` (Windows) or `mpv` (Linux/macOS) is in project directory or system PATH.

### Playlist download fails

- Verify `uv` is installed: `uv --version`
- Check `acestream-search` is available: `uv run acestream_search --help`
- Ensure internet connectivity

### Encoding issues

The application uses UTF-8 encoding. If you see garbled characters, ensure your system locale supports UTF-8.

## 📚 Dependencies

- **acestream-search** (≥1.6.2): Playlist source
- **customtkinter** (≥5.2.2): Modern UI components
- **ttkbootstrap** (≥1.14.7): Enhanced Tkinter themes
- **nuitka** (≥2.8.1): Python to native compiler

## 🙏 Acknowledgments

- [MPV](https://mpv.io/) - Excellent media player
- [Nuitka](https://nuitka.net/) - Python compiler
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [acestream-search](https://pypi.org/project/acestream-search/) - Playlist provider

---

**Built with ❤️ by a Senior Python Developer**
