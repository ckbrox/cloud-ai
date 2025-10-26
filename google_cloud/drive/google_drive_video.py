# @property
#     def resolution(self) -> tuple[int, int]:
#         if not self._resolution:
#             try:
#                 # Parse the media information from the stream
#                 media_info = MediaInfo.parse(self.file)

#                 # Find the video track and get the resolution
#                 for track in media_info.video_tracks:
#                     if track.width and track.height:
#                         self._resolution = (track.width, track.height)

#             except Exception as e:
#                 print(f"An error occurred: {e}")
#                 print("This could be due to incomplete or invalid MP4 data.")
#         return self._resolution