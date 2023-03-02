# dssb
dssb (Dmitry's Static Site Builder) is my personal static site builder, written in python. It generates the pages for my website, [ds0.xyz](https://ds0.xyz), which is then simply served with nginx.

dssb has minimal features that reflect my own needs. As such, it will likely only receive updates when I personally feel the need to implement a new feature for myself.

## Installation
The [latest release](https://github.com/dsvoid/dssb/releases) is available here for the moment. As it is not yet an installable package, you can try `dssb` for yourself by using its release binary. Currently, only a Linux build is present.

## Usage
dssb's `init` command will generate all the files necessary to deploy a new website by putting it in a folder named after the site.
    dssb init new_site
The contents of a newly initialized site are as follows:
```
new_site/
├─ content/
│  ├─ example_post.md
│  ├─ index.md
├─ static/
│  ├─ style.css
├─ templates/
│  ├─ archive.html
│  ├─ index.html
│  ├─ layout.html
│  ├─ post.html
│  ├─ tag_archive.html
│  ├─ tagged.html
```
The `content` folder contains Markdown (`.md`) files, each one representing a page in your website. The `index.md` file will become the home page, `index.html`: other files will become their own pages.

You can create a new page with the `page` command, which will create a file that dssb's site builder will be able to parse later:
    cd content/
    dssb page test_page.md
Each page has metadata. Open `test_page.md` in a text editor to see an example of its formatting:
```
---
title: "New Page"
---
# New Page
```
The metadata is demarcarted from the rest of the file with three dashes (`---`) at its beginning and end. No fields are really necessary for a page to function, but the presence of the metadata dashes is still mandatory for a page to be built. Currently only two fields can be used for pages:
- `title`: Used to fill out the `<title>` tag on the page. Defaults to the site folder name.
- `template`: the html file that will be filled with the content of the file. Defaults to the `layout.html` file in the `templates` folder.

dssb is purpose-built for blogging. Using the `post` command creates a markdown file with all the metadata currently necessary for a page to be considered a blog post by the site builder.
    dssb post test_post.md
Let's run through the metadata:
```
---
title: "New Post"
template: "post.html"
tags: []
publish_date: "yyyy-mm-dd"
---
```
- `template`: must be `post.html` to be considered a blog post at present.
- `tags`: an optional field to categorize your posts. Tags should be separated by commas and wrapped in double quotes. Example: `["hello", "world"]`.
- `publish_date`: year-month-day formatted string. This string is used to sort all blog posts by date when viewing the post archive or looking at posts with a specific tag.
It would be pretty cool if `publish_date` was autofilled, huh? I'll get around to it...

The default templates are what I've set up out of plain preferences for how my site displays. I encourage modifying it to suit your needs. Templates use custom values that are then replaced depending on the metadata provided by their content. The current values:
- `{{ site_name }}`: automatically retrieved from the site's folder name at present. I'd like to move this to a config file later.
- `{{ title }}`: the string used for the `<title>` tag. It's a combination of the `title` metadata and the `site_name`.
- `{{ template }}`: used in `layout.html` to load an inner template before rendering content. If no `template` is provided in a content file's metadata, the content is used directly.
- `{{ posts }}`: used by `archive.html` and `tagged.html` to list off all posts and posts with a specific tag, respectivley.
- `{{ tags }}`: used to list off either all tags in `tag_archive.html` or the specific `tags` of a blog post.
- `{{ publish_date }}`: used in blog post pages to show the content's `publish_date`.
- `{{ prev }}`: used in blog post pages to link to a post made before it, if it exists.
- `{{ next }}`: used in blog post pages to link to a post made after it, if it exists.

Finally, you can create a build of your static page with the `build` command. The site builder will generate the entire file structure and move it to a new `build/` folder which you can then drop in, say, your nginx configuration to host the site.

## Build and Develop
dssb's dependencies can be set up in a virtual environment: a `requirements.txt` file is provided for this.
```
git clone https://github.com/dsvoid/dssb.git
cd dssb
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
Further instructions assume you are still in the virtual environment

When not built, the application is run via `app.py` in the `src` folder.
    cd src
    python3 app.py --help

`pyinstaller` can be used to make a binary for the project. The contents fo the `defaults` folder are necessary for the build, so first generate a `.spec` file in the `src` folder:
    pyinstaller app.py --name dssb
After that, modify `dssb.spec` in a text editor to include the `defaults` folder using the `Tree()` function, right after the `a.binaries` line:
```
exe = EXE(
pyz,
a.scripts,
a.binaries,
Tree('../src/defaults', prefix='defaults/'),
```
Keep in mind that the arguments differ between Windows and Linux/Mac environments: use escaped backslashes (`\\`) in Windows.

Finally, run `pyinstaller` one last time on `dssb.spec` to generate your own binary:
```pyinstaller dssb.spec```
