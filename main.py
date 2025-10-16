# uv run nuitka --onefile --windows-console-mode=disable --enable-plugin=tk-inter main.py
"""
MPV Playlist Player - Professional Media Player Application
Author: Senior Python Developer
Description: High-performance M3U playlist player with MPV integration
"""

from pathlib import Path
from typing import Optional, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
from dataclasses import dataclass
from functools import lru_cache
import os
import threading


@dataclass(frozen=True, slots=True)
class Channel:
    """Immutable channel data structure for optimal memory usage."""
    index: int
    name: str
    url: str
    metadata: str


class M3UParser:
    """High-performance M3U playlist parser with lazy evaluation."""
    __slots__ = ('_path', '_encoding')
    
    _EXTINF_PATTERN = re.compile(r'^#EXTINF:-?\d+,(.+)$')
    
    def __init__(self, path: Path, encoding: str = 'utf-8'):
        self._path = path
        self._encoding = encoding
    
    @lru_cache(maxsize=1)
    def parse(self) -> Tuple[Channel, ...]:
        """Parse M3U file and return immutable tuple of channels."""
        with self._path.open('r', encoding=self._encoding, errors='ignore') as f:
            lines = tuple(line.strip() for line in f if line.strip())
        return tuple(self._parse_channels(lines))
    
    def _parse_channels(self, lines: Tuple[str, ...]) -> List[Channel]:
        """Parse channel data from lines using generator pattern."""
        channels = []
        i, idx = 0, 1
        
        while i < len(lines):
            if lines[i].startswith('#EXTINF'):
                match = self._EXTINF_PATTERN.match(lines[i])
                if match and i + 1 < len(lines):
                    name = match.group(1)
                    url = lines[i + 1]
                    metadata = self._extract_metadata(name)
                    channels.append(Channel(idx, name, url, metadata))
                    idx += 1
                    i += 2
                    continue
            i += 1
        
        return channels
    
    @staticmethod
    def _extract_metadata(name: str) -> str:
        """Extract category metadata from channel name."""
        match = re.search(r'\[(.*?)\]', name)
        return match.group(1) if match else ''


class PlaylistDownloader:
    """Handles playlist download from acestream_search with progress tracking."""
    __slots__ = ('_playlist_path',)
    
    def __init__(self, playlist_path: Path = Path('playlist.m3u')):
        self._playlist_path = playlist_path
    
    def download_playlist(self, progress_callback=None) -> Tuple[bool, str]:
        """Execute acestream_search and save to playlist.m3u with UTF-8 encoding."""
        try:
            # Clear existing playlist
            if self._playlist_path.exists():
                self._playlist_path.unlink()
            
            # Set UTF-8 environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            if progress_callback:
                progress_callback(0, 'Starting download...')
            
            # Execute uv run acestream_search
            process = subprocess.Popen(
                ['acestream_search'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # Collect output with progress tracking
            output_lines = []
            stream_count = 0
            estimated_total = 2100
            
            for line in process.stdout:
                output_lines.append(line)
                # Count EXTINF lines for progress
                if line.startswith('#EXTINF'):
                    stream_count += 1
                    if progress_callback and stream_count % 50 == 0:
                        progress = min(95, (stream_count / estimated_total) * 100)
                        progress_callback(progress, f'Loading streams: {stream_count}/{estimated_total}')
            
            process.wait()
            
            if progress_callback:
                progress_callback(98, 'Saving playlist...')
            
            if process.returncode == 0 and output_lines:
                output = ''.join(output_lines)
                self._playlist_path.write_text(output, encoding='utf-8')
                
                if progress_callback:
                    progress_callback(100, f'Completed! Loaded {stream_count} streams')
                
                return True, f'Playlist saved: {stream_count} streams loaded'
            
            stderr = process.stderr.read() if process.stderr else ''
            return False, f'Failed to download playlist: {stderr}'
            
        except FileNotFoundError:
            return False, 'uv command not found. Please ensure uv is installed.'
        except Exception as e:
            return False, f'Error downloading playlist: {str(e)}'


class MPVController:
    """MPV player process manager with optimal resource handling."""
    __slots__ = ('_mpv_path', '_process', '_current_url')
    
    def __init__(self, mpv_path: Path = Path('mpv.exe')):
        self._mpv_path = mpv_path
        self._process: Optional[subprocess.Popen] = None
        self._current_url: str = ''
    
    def play(self, url: str, title: str = '') -> bool:
        """Start MPV player with specified URL."""
        self.stop()
        
        if not self._mpv_path.exists():
            return False
        
        try:
            args = [
                str(self._mpv_path),
                url,
                '--force-window=yes',
                '--keep-open=yes',
                '--no-terminal',
                f'--title={title}' if title else ''
            ]
            
            self._process = subprocess.Popen(
                [arg for arg in args if arg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            self._current_url = url
            return True
            
        except Exception:
            return False
    
    def stop(self) -> None:
        """Terminate current MPV process."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
        self._process = None
        self._current_url = ''
    
    @property
    def is_playing(self) -> bool:
        """Check if MPV process is active."""
        return self._process is not None and self._process.poll() is None


class ProgressDialog(tk.Toplevel):
    """Modern progress dialog for playlist download."""
    
    __slots__ = ('_progress_var', '_status_var', '_progressbar', '_cancel_flag', '_percent_label')
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Downloading Playlist')
        self.geometry('500x150')
        self.resizable(False, False)
        self.configure(bg='#1e1e1e')
        self.transient(parent)
        self.grab_set()
        
        self._cancel_flag = False
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (150 // 2)
        self.geometry(f'+{x}+{y}')
        
        # Status label
        self._status_var = tk.StringVar(value='Initializing...')
        status_label = tk.Label(
            self,
            textvariable=self._status_var,
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Segoe UI', 10)
        )
        status_label.pack(pady=20)
        
        # Progress bar
        self._progress_var = tk.DoubleVar(value=0)
        self._progressbar = ttk.Progressbar(
            self,
            variable=self._progress_var,
            maximum=100,
            length=450,
            mode='determinate'
        )
        self._progressbar.pack(pady=10)
        
        # Percentage label
        self._percent_label = tk.Label(
            self,
            text='0%',
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Segoe UI', 9)
        )
        self._percent_label.pack(pady=5)
        
        self.protocol('WM_DELETE_WINDOW', self._on_cancel)
    
    def update_progress(self, progress: float, status: str):
        """Update progress bar and status."""
        self._progress_var.set(progress)
        self._status_var.set(status)
        self._percent_label.config(text=f'{int(progress)}%')
        self.update_idletasks()
    
    def _on_cancel(self):
        """Handle cancel request."""
        self._cancel_flag = True
        self.destroy()


class ModernPlaylistPlayer(tk.Tk):
    """Professional MPV playlist player with modern UI design."""
    
    # Color scheme - Modern dark theme
    COLORS = {
        'bg': '#1e1e1e',
        'fg': '#ffffff',
        'accent': '#007acc',
        'hover': '#2d2d30',
        'selected': '#094771',
        'border': '#3e3e42',
        'button_bg': '#0e639c',
        'button_hover': '#1177bb',
        'refresh_bg': '#16825d',
        'refresh_hover': '#1a9870'
    }
    
    __slots__ = ('_parser', '_mpv', '_channels', '_tree', '_search_var',
                 '_status_var', '_filter_var', '_style', '_downloader', '_channel_map')
    
    def __init__(self):
        super().__init__()
        self.title('MPV Playlist Player Pro')
        self.geometry('1200x700')
        self.configure(bg=self.COLORS['bg'])
        
        self._mpv = MPVController()
        self._downloader = PlaylistDownloader()
        self._parser: Optional[M3UParser] = None
        self._channels: Tuple[Channel, ...] = ()
        self._channel_map: dict = {}  # Map tree items to channels
        
        self._setup_styles()
        self._create_widgets()
        self._setup_bindings()
        
        # Auto-download playlist on startup
        self.after(100, self._download_and_load_playlist)
    
    def _setup_styles(self) -> None:
        """Configure ttk styles for modern appearance."""
        self._style = ttk.Style()
        self._style.theme_use('clam')
        
        # Treeview style
        self._style.configure(
            'Modern.Treeview',
            background=self.COLORS['bg'],
            foreground=self.COLORS['fg'],
            fieldbackground=self.COLORS['bg'],
            borderwidth=0,
            font=('Segoe UI', 10),
            rowheight=25
        )
        
        self._style.map('Modern.Treeview',
                       background=[('selected', self.COLORS['selected'])],
                       foreground=[('selected', self.COLORS['fg'])])
        
        # Heading style
        self._style.configure(
            'Modern.Treeview.Heading',
            background=self.COLORS['hover'],
            foreground=self.COLORS['fg'],
            borderwidth=1,
            relief='flat',
            font=('Segoe UI', 10, 'bold')
        )
        
        # Frame style
        self._style.configure('Modern.TFrame', background=self.COLORS['bg'])
        
        # Entry style
        self._style.configure(
            'Modern.TEntry',
            fieldbackground=self.COLORS['hover'],
            foreground=self.COLORS['fg'],
            borderwidth=1,
            relief='flat'
        )
    
    def _create_widgets(self) -> None:
        """Build UI components with modern design."""
        # Top control panel
        top_frame = ttk.Frame(self, style='Modern.TFrame', padding=10)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Refresh playlist button
        refresh_btn = tk.Button(
            top_frame,
            text='🔄 Refresh Playlist',
            command=self._download_and_load_playlist,
            bg=self.COLORS['refresh_bg'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground=self.COLORS['refresh_hover'],
            activeforeground=self.COLORS['fg']
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Search frame
        search_frame = ttk.Frame(top_frame, style='Modern.TFrame')
        search_frame.pack(side='left', fill='x', expand=True, padx=20)
        
        tk.Label(
            search_frame,
            text='🔍',
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 12)
        ).pack(side='left', padx=(0, 5))
        
        self._search_var = tk.StringVar()
        self._search_var.trace('w', lambda *_: self._filter_channels())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            bg=self.COLORS['hover'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 10),
            relief='flat',
            insertbackground=self.COLORS['fg']
        )
        search_entry.pack(side='left', fill='x', expand=True, ipady=6)
        
        # Filter dropdown
        self._filter_var = tk.StringVar(value='All Categories')
        filter_menu = ttk.Combobox(
            top_frame,
            textvariable=self._filter_var,
            state='readonly',
            font=('Segoe UI', 9),
            width=20
        )
        filter_menu.pack(side='right', padx=5)
        filter_menu.bind('<<ComboboxSelected>>', lambda _: self._filter_channels())
        filter_menu['values'] = ('All Categories',)
        
        # Main content area
        content_frame = ttk.Frame(self, style='Modern.TFrame')
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(content_frame, style='Modern.TFrame')
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(tree_frame, bg=self.COLORS['bg'])
        scrollbar.pack(side='right', fill='y')
        
        # Modified columns - removed URL display
        self._tree = ttk.Treeview(
            tree_frame,
            columns=('name', 'category'),
            show='headings',
            style='Modern.Treeview',
            selectmode='browse',
            yscrollcommand=scrollbar.set
        )
        
        self._tree.heading('name', text='Channel Name', anchor='w')
        self._tree.heading('category', text='Category', anchor='w')
        
        self._tree.column('name', width=800, minwidth=400)
        self._tree.column('category', width=300, minwidth=150)
        
        self._tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._tree.yview)
        
        # Bottom control panel
        bottom_frame = ttk.Frame(self, style='Modern.TFrame', padding=10)
        bottom_frame.pack(fill='x', padx=5, pady=5)
        
        # Play/Stop buttons
        play_btn = tk.Button(
            bottom_frame,
            text='▶ Play',
            command=self._play_selected,
            bg=self.COLORS['button_bg'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            activebackground=self.COLORS['button_hover'],
            activeforeground=self.COLORS['fg']
        )
        play_btn.pack(side='left', padx=5)
        
        stop_btn = tk.Button(
            bottom_frame,
            text='⏹ Stop',
            command=self._stop_playback,
            bg='#d13438',
            fg=self.COLORS['fg'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=30,
            pady=8,
            cursor='hand2',
            activebackground='#e81123',
            activeforeground=self.COLORS['fg']
        )
        stop_btn.pack(side='left', padx=5)
        
        # Status bar
        self._status_var = tk.StringVar(value='Initializing...')
        status_label = tk.Label(
            bottom_frame,
            textvariable=self._status_var,
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 9),
            anchor='w'
        )
        status_label.pack(side='right', fill='x', expand=True, padx=10)
    
    def _setup_bindings(self) -> None:
        """Configure event handlers."""
        self._tree.bind('<Double-Button-1>', lambda _: self._play_selected())
        self._tree.bind('<Return>', lambda _: self._play_selected())
        self.protocol('WM_DELETE_WINDOW', self._on_closing)
    
    def _download_and_load_playlist(self) -> None:
        """Download playlist from acestream_search with progress dialog."""
        progress_dialog = ProgressDialog(self)
        
        def download_thread():
            try:
                success, message = self._downloader.download_playlist(
                    progress_callback=lambda p, s: progress_dialog.update_progress(p, s)
                )
                
                self.after(100, lambda: self._on_download_complete(progress_dialog, success, message))
            except Exception as e:
                self.after(100, lambda: self._on_download_complete(progress_dialog, False, str(e)))
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _on_download_complete(self, dialog: ProgressDialog, success: bool, message: str):
        """Handle download completion."""
        dialog.destroy()
        
        if success:
            # Clear existing playlist data
            self._channels = ()
            self._channel_map.clear()
            self._tree.delete(*self._tree.get_children())
            self._search_var.set('')
            self._filter_var.set('All Categories')
            
            # Load new playlist
            self._load_playlist(Path('playlist.m3u'))
        else:
            messagebox.showerror('Download Error', message)
            self._status_var.set('Download failed')
    
    def _load_playlist(self, path: Path) -> None:
        """Load and parse M3U playlist file."""
        try:
            self._parser = M3UParser(path)
            self._channels = self._parser.parse()
            self._populate_tree()
            self._update_filter_menu()
            self._status_var.set(f'✓ Loaded {len(self._channels)} channels from {path.name}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load playlist:\n{str(e)}')
            self._status_var.set('Error loading playlist')
    
    def _populate_tree(self, channels: Optional[Tuple[Channel, ...]] = None) -> None:
        """Populate treeview with channel data (without URLs) and map to channel objects."""
        self._tree.delete(*self._tree.get_children())
        self._channel_map.clear()
        display_channels = channels if channels is not None else self._channels
        
        for channel in display_channels:
            # Insert channel data without URL display
            item_id = self._tree.insert(
                '',
                'end',
                values=(channel.name, channel.metadata)
            )
            # Map tree item to channel object for URL retrieval
            self._channel_map[item_id] = channel
    
    def _update_filter_menu(self) -> None:
        """Update category filter dropdown."""
        categories = {'All Categories'}
        categories.update(ch.metadata for ch in self._channels if ch.metadata)
        
        filter_widget = None
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Combobox):
                        filter_widget = subchild
                        break
        
        if filter_widget:
            filter_widget['values'] = tuple(sorted(categories))
    
    def _filter_channels(self) -> None:
        """Filter channels based on search and category."""
        search_text = self._search_var.get().lower()
        category = self._filter_var.get()
        
        filtered = tuple(
            ch for ch in self._channels
            if (search_text in ch.name.lower() or search_text in ch.url.lower())
            and (category == 'All Categories' or ch.metadata == category)
        )
        
        self._populate_tree(filtered)
        self._status_var.set(f'Showing {len(filtered)} of {len(self._channels)} channels')
    
    def _play_selected(self) -> None:
        """Play selected channel in MPV using channel map."""
        selection = self._tree.selection()
        
        if not selection:
            messagebox.showwarning('Warning', 'Please select a channel to play')
            return
        
        item_id = selection[0]
        channel = self._channel_map.get(item_id)
        
        if not channel:
            messagebox.showerror('Error', 'Invalid channel selection')
            return
        
        if self._mpv.play(channel.url, channel.name):
            self._status_var.set(f'▶ Playing: {channel.name}')
        else:
            messagebox.showerror('Error', 'MPV player not found.\nPlease ensure mpv.exe is in the project folder')
            self._status_var.set('Playback failed')
    
    def _stop_playback(self) -> None:
        """Stop current playback."""
        self._mpv.stop()
        self._status_var.set('⏹ Playback stopped')
    
    def _on_closing(self) -> None:
        """Clean up resources on window close."""
        self._mpv.stop()
        self.destroy()


if __name__ == '__main__':
    app = ModernPlaylistPlayer()
    app.mainloop()
