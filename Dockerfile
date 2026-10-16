# Hugging Face Spaces (Docker SDK) deployment for the EcoFoodSystems dashboard.
# Containers on Spaces run as UID 1000 - create a matching user before
# copying anything in, so file ownership and pip installs don't hit
# permission errors. See: https://huggingface.co/docs/hub/spaces-sdks-docker
FROM python:3.11-slim

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
# for exactly this. One worker to start: each worker is a separate process
# that re-loads all of data_access.py's dataframes/geojsons into its own
# memory independently, so more workers multiplies memory use, not just
# throughput - raise this only after confirming real headroom on the
# deployed instance, not by guessing. --timeout raised from gunicorn's 30s
# default since some callbacks (isochrone/geospatial rendering) are slow.
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "120", "app:server"]
