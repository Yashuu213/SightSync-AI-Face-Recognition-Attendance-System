# Gunicorn configuration file
import multiprocessing

# We need a longer timeout because face_recognition (dlib) can take
# 30-60 seconds to process 10 high-resolution frames on a Free CPU tier.
timeout = 120

# Workers
workers = 1
threads = 2

# Increase max request line and header sizes to allow large base64 JSON payloads
limit_request_line = 8190
limit_request_field_size = 16384
