# Hugging Face Spaces (Docker SDK) deployment for the EcoFoodSystems dashboard.
# Containers on Spaces run as UID 1000 - create a matching user before
# copying anything in, so file ownership and pip installs don't hit
# permission errors. See: https://huggingface.co/docs/hub/spaces-sdks-docker
FROM python:3.11-slim

# rasterio/rioxarray's manylinux wheels dynamically link against libexpat at
# runtime even though it's not a build-time pip dependency - python:3.11-slim
# doesn't ship it, so the container built and started but crashed on import.
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements first so Docker caches the (slow) dependency-install
# layer separately from the app code, which changes far more often - avoids
# a full reinstall on every push that only touches a .py file.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 7860

# gunicorn (already in requirements.txt) instead of app.py's own
# `app.run(debug=...)` dev-server path - app.py exposes `server = app.server`
# for exactly this.
#
# --workers 2: the safe ceiling on CPU-basic's 2 vCPU / 16GB RAM - raise
# further only after upgrading the hardware tier.
# --preload: loads the app (and all of data_access.py's dataframes/geojsons)
# once in the master process BEFORE forking workers, so both workers share
# that memory via copy-on-write instead of each separately re-importing and
# re-loading ~255MB of CSVs/geojsons on boot.
# --worker-class gthread --threads 4: adds lightweight concurrency within
# each worker for I/O-bound work (file reads, the chatbot's Groq API calls)
# on top of the 2 process workers. Confirmed safe - matplotlib/seaborn are
# only touched once at import time (a colormap lookup), never inside a
# live callback, so there's no per-request matplotlib global-state hazard.
# --max-requests/--max-requests-jitter: periodically recycles each worker
# to guard against memory creep over hours of live use; a recycled worker
# re-forks from the already-preloaded master, so it's not a cold restart.
# --timeout raised from gunicorn's 30s default since some callbacks
# (isochrone/geospatial rendering) are slow. --keep-alive set explicitly
# to avoid dropped connections on those same slow callbacks.
CMD ["gunicorn", "--bind", "0.0.0.0:7860", \
     "--workers", "2", "--worker-class", "gthread", "--threads", "4", \
     "--preload", "--timeout", "120", "--keep-alive", "5", \
     "--max-requests", "500", "--max-requests-jitter", "50", \
     "app:server"]
