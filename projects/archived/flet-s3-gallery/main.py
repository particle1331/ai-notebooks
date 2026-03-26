# from flask import Flask, request, render_template_string
# import boto3

# app = Flask(__name__)
# s3 = boto3.client("s3")

# PAGE_SIZE = 20

# TEMPLATE = """
# <h2>Bucket: {{ bucket }}</h2>

# <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
# {% for obj in objects %}
#   {% if obj.key.endswith(('.jpg','.png','.jpeg','.webp')) %}
#     <img src="{{ obj.url }}" width="200"/>
#   {% elif obj.key.endswith(('.mp4','.webm')) %}
#     <video width="200" controls>
#       <source src="{{ obj.url }}">
#     </video>
#   {% endif %}
# {% endfor %}
# </div>

# <br>
# {% if token %}
#   <a href="/?bucket={{ bucket }}&token={{ token | urlencode }}">Next page</a>
# {% endif %}
# """

# @app.route("/")
# def index():
#     bucket = request.args.get("bucket")
#     token = request.args.get("token")

#     if not bucket:
#         return "Provide ?bucket=BUCKET_NAME"

#     params = {
#         "Bucket": bucket,
#         "MaxKeys": PAGE_SIZE,
#     }
#     if token:
#         params["ContinuationToken"] = token

#     resp = s3.list_objects_v2(**params)

#     objects = []
#     for item in resp.get("Contents", []):
#         key = item["Key"]
#         if not key.lower().endswith((
#             ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"
#         )):
#             continue

#         url = s3.generate_presigned_url(
#             "get_object",
#             Params={"Bucket": bucket, "Key": key},
#             ExpiresIn=300,
#         )
#         objects.append({"key": key, "url": url})

#     return render_template_string(
#         TEMPLATE,
#         bucket=bucket,
#         objects=objects,
#         token=resp.get("NextContinuationToken"),
#     )

# if __name__ == "__main__":
#     app.run(debug=True)

import math
import flet as ft
import boto3

PAGE_SIZE = 12
MEDIA_EXT = (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm")

session = boto3.Session()
s3 = session.client("s3")


def main(page: ft.Page):
    page.title = "S3 Media Viewer"
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    bucket_field = ft.TextField(label="Bucket name", width=400)
    load_btn = ft.ElevatedButton("Load")

    grid = ft.GridView(
        expand=True,
        runs_count=4,
        max_extent=240,
        spacing=10,
        run_spacing=10,
    )

    # Pagination state
    all_keys = []
    total_pages = 0
    current_page = 1

    page_select = ft.Dropdown(width=150)
    prev_btn = ft.ElevatedButton("Prev")
    next_btn = ft.ElevatedButton("Next")

    # ----------- Load ALL KEYS once -----------
    def load_all_keys(bucket: str):
        nonlocal all_keys, total_pages

        all_keys = []
        token = None

        while True:
            params = {"Bucket": bucket, "MaxKeys": 1000}
            if token:
                params["ContinuationToken"] = token

            resp = s3.list_objects_v2(**params)

            for obj in resp.get("Contents", []):
                key = obj["Key"]
                if key.lower().endswith(MEDIA_EXT):
                    all_keys.append(key)

            token = resp.get("NextContinuationToken")
            if not token:
                break

        total_pages = max(1, math.ceil(len(all_keys) / PAGE_SIZE))

    # ----------- Load a specific page -----------
    def load_page(page_index: int):
        nonlocal current_page
        current_page = page_index

        grid.controls.clear()

        start = (page_index - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_keys = all_keys[start:end]

        bucket = bucket_field.value

        for key in page_keys:
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=300,
            )

            if key.lower().endswith((".mp4", ".webm")):
                ctrl = ft.Video(
                    src=url,
                    width=220,
                    height=180,
                    fit=ft.VideoFit.CONTAIN,
                )
            else:
                ctrl = ft.Image(
                    src=url,
                    width=220,
                    height=180,
                    fit=ft.BoxFit.CONTAIN,
                )

            grid.controls.append(ctrl)

        update_pagination_controls()
        page.update()

    # ----------- Update dropdown + buttons -----------
    def update_pagination_controls():
        page_select.options = [
            ft.dropdown.Option(str(i)) for i in range(1, total_pages + 1)
        ]
        page_select.value = str(current_page)

        prev_btn.disabled = current_page == 1
        next_btn.disabled = current_page == total_pages

    # ----------- Event handlers -----------
    def start_load(e):
        bucket = bucket_field.value
        if not bucket:
            return

        load_all_keys(bucket)
        load_page(1)

    def prev(e):
        if current_page > 1:
            load_page(current_page - 1)

    def next_(e):
        if current_page < total_pages:
            load_page(current_page + 1)

    def jump(e):
        load_page(int(e.control.value))

    # Bind events
    prev_btn.on_click = prev
    next_btn.on_click = next_
    load_btn.on_click = start_load
    page_select.on_change = jump

    # Layout
    page.add(
        ft.Row([bucket_field, load_btn]),
        ft.Row([prev_btn, page_select, next_btn]),
        grid,
    )


ft.app(target=main)
