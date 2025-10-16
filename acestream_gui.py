
import customtkinter as ctk
import subprocess
import re
from pathlib import Path
from functools import partial
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True, slots=True)
class Channel:
    """Immutable channel data structure for memory efficiency"""
    index: int
    name: str
    country: str
    categories: str
    timestamp: str
    score_a: float
    score_b: int
    url: str
    
    @property
    def display_text(self) -> str:
        return f"{self.index}. {self.name} [{self.country}] • Score: {self.score_a:.3f}"


class M3UParser:
    """High-performance M3U playlist parser with functional approach"""
    
    __slots__ = ('_pattern_extinf', '_pattern_url')
    
    def __init__(self):
        self._pattern_extinf = re.compile(
            r'#EXTINF:-1,(\d+)\.\s+(.+?)\s+\[(\w+)\]\s+\[\s*(.+?)\s*\]\s+'
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+a=([\d.]+)\s+b=(\d+)'
        )
        self._pattern_url = re.compile(r'http://[^\s]+')
    
    def parse(self, content: str) -> List[Channel]:
        """Parse M3U content into Channel objects using functional approach"""
        lines = content.strip().split('\n')
        pairs = zip(
            filter(lambda l: l.startswith('#EXTINF'), lines),
            filter(lambda l: l.startswith('http://'), lines)
        )
        
        return list(filter(None, map(self._create_channel, pairs)))
    
    def _create_channel(self, pair: Tuple[str, str]) -> Channel | None:
        """Create Channel from EXTINF and URL pair"""
        extinf, url = pair
        match = self._pattern_extinf.search(extinf)
        return match and Channel(
            index=int(match.group(1)),
            name=match.group(2),
            country=match.group(3),
            categories=match.group(4),
            timestamp=match.group(5),
            score_a=float(match.group(6)),
            score_b=int(match.group(7)),
            url=url.strip()
        )


class ModernPlaylistGUI(ctk.CTk):
    """Modern AceStream playlist viewer with professional styling"""
    
    __slots__ = ('parser', 'channels', 'search_var', 
                 'scrollable_frame', 'status_label', 'mpv_path', 'header_label',
                 'playlist_path')
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.parser = M3UParser()
        self.channels: List[Channel] = []
        self.mpv_path = Path('./mpv.exe')
        self.playlist_path = Path('playlist.m3u')
        
        # Theme setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Window setup
        self.title("AceStream Playlist Viewer")
        self.geometry("900x700")
        self._setup_ui()
        self._load_playlist()
    
    def _setup_ui(self):
        """Build UI components with modern styling"""
        # Header with gradient effect
        header = ctk.CTkFrame(self, fg_color=("#1e3a5f", "#0d1b2a"), corner_radius=15)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        self.header_label = ctk.CTkLabel(
            header,
            text="🎬 AceStream Channels",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#00d9ff", "#4cc9f0")
        )
        self.header_label.pack(pady=15)
        
        # Control panel
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_channels())
        
        search_entry = ctk.CTkEntry(
            control_frame,
            placeholder_text="🔍 Search channels by name, country or category...",
            textvariable=self.search_var,
            height=45,
            font=ctk.CTkFont(size=14),
            corner_radius=12,
            border_width=2,
            border_color=("#00b4d8", "#0077b6")
        )
        search_entry.pack(fill="x", side="left", expand=True, padx=(0, 10))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_frame.pack(side="right")
        
        # Update button (runs BAT file)
        ctk.CTkButton(
            buttons_frame,
            text="⚡ Update",
            command=self._update_playlist,
            width=100,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#e63946", "#d62828"),
            hover_color=("#c1121f", "#9d0208"),
            corner_radius=12
        ).pack(side="left", padx=(0, 5))
        
        # Refresh button (reads M3U file)
        ctk.CTkButton(
            buttons_frame,
            text="↻ Refresh",
            command=self._load_playlist,
            width=100,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#00b4d8", "#0077b6"),
            hover_color=("#0096c7", "#005f8c"),
            corner_radius=12
        ).pack(side="left")
        
        # Scrollable channel list
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=("#1a1a1a", "#0a0a0a"),
            corner_radius=15,
            border_width=2,
            border_color=("#2b2b2b", "#1a1a1a")
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Status bar
        status_frame = ctk.CTkFrame(self, fg_color=("#1e3a5f", "#0d1b2a"), height=40, corner_radius=12)
        status_frame.pack(fill="x", padx=20, pady=(0, 15))
        status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#4cc9f0", "#00d9ff")
        )
        self.status_label.pack(pady=8)
    
    def _update_playlist(self):
        """Run BAT file to update playlist"""
        self.status_label.configure(text="⚡ Updating playlist from AceStream...")
        self.update()
        
        try:
            # Run batch file
            result = subprocess.run(
                ['save_playlist.bat'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd='.',
                shell=True
            )
            
            if result.returncode == 0:
                self.status_label.configure(
                    text="✓ Playlist updated successfully",
                    text_color=("#4cc9f0", "#00d9ff")
                )
                # Auto-load after update
                self.after(500, self._load_playlist)
            else:
                self.status_label.configure(
                    text=f"⚠ Update warning: check save_playlist.bat",
                    text_color=("#ffc107", "#ff9800")
                )
                
        except subprocess.TimeoutExpired:
            self.status_label.configure(
                text="⚠ Update timeout (>60s)",
                text_color=("#ff6b6b", "#ff5252")
            )
        except FileNotFoundError:
            self.status_label.configure(
                text="✗ save_playlist.bat not found",
                text_color=("#ff6b6b", "#ff5252")
            )
        except Exception as e:
            self.status_label.configure(
                text=f"✗ Update error: {str(e)[:40]}",
                text_color=("#ff6b6b", "#ff5252")
            )
    
    def _load_playlist(self):
        """Load and parse playlist from M3U file"""
        self.status_label.configure(text="⏳ Loading playlist from file...")
        self.update()
        
        try:
            # Read M3U file
            if not self.playlist_path.exists():
                self.status_label.configure(
                    text="⚠ playlist.m3u not found. Click 'Update' first.",
                    text_color=("#ffc107", "#ff9800")
                )
                return
            
            content = self.playlist_path.read_text(encoding='utf-8')
            self.channels = self.parser.parse(content)
            self._display_channels(self.channels)
            
            self.status_label.configure(
                text=f"✓ Loaded {len(self.channels)} channels from {self.playlist_path.name}",
                text_color=("#4cc9f0", "#00d9ff")
            )
            self.header_label.configure(
                text=f"🎬 AceStream Channels ({len(self.channels)})"
            )
            
        except UnicodeDecodeError:
            try:
                # Try with cp1251 if UTF-8 fails
                content = self.playlist_path.read_text(encoding='cp1251')
                self.channels = self.parser.parse(content)
                self._display_channels(self.channels)
                self.status_label.configure(
                    text=f"✓ Loaded {len(self.channels)} channels (cp1251)",
                    text_color=("#4cc9f0", "#00d9ff")
                )
            except Exception as e:
                self.status_label.configure(
                    text=f"✗ Encoding error: {str(e)[:40]}",
                    text_color=("#ff6b6b", "#ff5252")
                )
        except Exception as e:
            self.status_label.configure(
                text=f"✗ Load error: {str(e)[:50]}",
                text_color=("#ff6b6b", "#ff5252")
            )
    
    def _display_channels(self, channels: List[Channel]):
        """Display channels with modern card-style buttons"""
        # Clear existing widgets safely
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create channel cards
        tuple(map(self._create_channel_card, channels))
    
    def _create_channel_card(self, channel: Channel):
        """Create styled card for a channel"""
        # Card container
        card = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=("#2b2b2b", "#1a1a1a"),
            corner_radius=12,
            border_width=2,
            border_color=("#404040", "#2a2a2a")
        )
        card.pack(fill="x", pady=5, padx=5)
        
        # Main button
        button = ctk.CTkButton(
            card,
            text=channel.display_text,
            command=partial(self._play_channel, channel),
            height=55,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("transparent", "transparent"),
            hover_color=("#00b4d8", "#0077b6"),
            corner_radius=10,
            anchor="w",
            text_color=("#ffffff", "#e0e0e0")
        )
        button.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Category badge
        badge = ctk.CTkLabel(
            button,
            text=f"📂 {channel.categories}",
            font=ctk.CTkFont(size=11),
            text_color=("#00d9ff", "#4cc9f0"),
            fg_color=("#1a1a1a", "#0a0a0a"),
            corner_radius=8,
            padx=10,
            pady=3
        )
        badge.place(relx=0.98, rely=0.5, anchor="e")
    
    def _filter_channels(self):
        """Filter channels based on search query"""
        query = self.search_var.get().lower()
        filtered = list(filter(
            lambda ch: any(map(
                lambda field: query in str(field).lower(),
                (ch.name, ch.country, ch.categories)
            )),
            self.channels
        )) if query else self.channels
        
        self._display_channels(filtered)
        self.status_label.configure(
            text=f"Found {len(filtered)} / {len(self.channels)} channels",
            text_color=("#4cc9f0", "#00d9ff")
        )
    
    def _play_channel(self, channel: Channel):
        """Launch MPV player with selected channel"""
        self.status_label.configure(
            text=f"▶ Playing: {channel.name}",
            text_color=("#4cc9f0", "#00d9ff")
        )
        
        try:
            subprocess.Popen(
                [str(self.mpv_path), channel.url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            self.status_label.configure(
                text="✗ MPV not found in current directory",
                text_color=("#ff6b6b", "#ff5252")
            )


def main():
    """Application entry point"""
    app = ModernPlaylistGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
