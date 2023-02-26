import os
import sys
import shutil
import markdown
import json
import argparse
from pathlib import Path

class Builder:
    site_name = ""
    site_dir = ""
    site_metadata = {}
    sorted_posts = []
    other_pages = []
    tags = {}
    
    def __init__(self):
        return

    def new_site(self,site_name):
        app_dir = os.path.dirname(os.path.realpath(__file__))
        self.site_name = site_name
        self.site_dir = f"{os.getcwd()}/{site_name}"
        if not os.path.exists(self.site_dir):
            try:
                os.makedirs(self.site_dir)
                shutil.copytree(f"{app_dir}/defaults/content/",f"{self.site_dir}/content/")
                shutil.copytree(f"{app_dir}/defaults/static/",f"{self.site_dir}/static/")
                shutil.copytree(f"{app_dir}/defaults/templates/",f"{self.site_dir}/templates/")
            except OSError as error:
                print(f"[E] Aborted initializing new site: OSError encountered.\n{error}")
                return
        else:
            print(f"[E] Aborted building new site: directory {self.site_name} already exists.")
            return
        print(f"Initialized new site {site_name}.\nTo build, run the following command:\ndssb build -d {site_name}")

    def build_site(self,dir):
        if not self.site_name:
            self.site_name = dir.rstrip("/").split("/")[-1]
        if not self.site_dir:
            self.site_dir = dir.rstrip("/")
        content_dir = f"{self.site_dir}/content"
        templates_dir = f"{self.site_dir}/templates"
        static_dir = f"{self.site_dir}/static"
        if not os.path.exists(content_dir):
            print("[E] Aborted building site: content directory not found here.")
            return
        if not os.path.exists(templates_dir):
            print("[E] Aborted building site: templates directory not found here.")
            return
        if not os.path.exists(static_dir):
            print("[E] Aborted building site: static directory not found here.")
            return
        content_files = os.listdir(content_dir)
        print("Collecting site metadata...")
        for content_file in content_files:
            file_metadata = self.read_metadata(content_file)
            file_metadata["filename"] = "".join(content_file.split(".")[:-1]) # assuming all files have extensions.
            if not file_metadata:
                print(f"[W] Failed to build page {content_file}: improperly formatted metadata.")
                continue
            if ("template" in file_metadata) and (file_metadata["template"] == "post.html"):
                self.sorted_posts.append(file_metadata)
            else:
                self.other_pages.append(file_metadata)
        print("Building pages...")
        self.sorted_posts = sorted(self.sorted_posts, key=lambda v: v["publish_date"], reverse=True)
        for i in range(len(self.sorted_posts)):
            post = self.sorted_posts[i]
            post["index"] = i
            if "tags" in post:
                for tag in post["tags"]:
                    if tag not in self.tags:
                        self.tags[tag] = [i]
                    else:
                        self.tags[tag].append(i)
            self.build_post(post)
        for page in self.other_pages:
            self.build_page(page)
        print("Building archives and tags...")
        self.build_archive()
        self.build_tag_archive()
        for tag in self.tags:
            self.build_tag(tag)
        print("Building static files...")
        shutil.copytree(f"{self.site_dir}/static/",f"{self.site_dir}/build/static/",dirs_exist_ok=True)
        print(f"Finished building {self.site_name}.\nContents in '{self.site_dir}/build'.\nTo test locally run the following:")
        print(f"python3 -m http.server --directory {self.site_dir}/build")

    def read_metadata(self,content_file):
        file_metadata = {}
        metadata_tag_closed = True
        with open(f"{self.site_dir}/content/{content_file}") as f:
            if f.readline().strip() != "---": # check for start of metadata
                return False
            metadata_line = f.readline().strip()
            while metadata_line != "---":
                if not metadata_line: # end of file reached without end of metadata tag
                    metadata_tag_closed = False
                    break
                try:
                    metadata_key = metadata_line.split(":")[0].strip()
                    metadata_value = json.loads(metadata_line.split(":")[1].strip())
                    file_metadata[metadata_key] = metadata_value
                except json.decoder.JSONDecodeError:
                    return False
                except IndexError:
                    return False
                metadata_line = f.readline().strip()
        if not file_metadata:
            return "no metadata"
        if not metadata_tag_closed:
            return False
        return file_metadata

    def build_page(self,file_metadata):
        result = ""
        with open(f"{self.site_dir}/templates/layout.html") as f:
            result = f.read()
        result = result.replace("{{ site_name }}", self.site_name)
        if "template" in file_metadata:
            template = self.read_template(file_metadata["template"])
            result = result.replace("{{ template }}",template)
        else:
            result = result.replace("{{ template }}","{{ content }}")
        if "title" in file_metadata:
            result = result.replace("{{ title }}", f"{file_metadata['title']} - {self.site_name}")
        else:
            result = result.replace("{{ title }}", self.site_name)
        with open(f"{self.site_dir}/content/{file_metadata['filename']}.md") as f:
            content = markdown.markdown(f.read(),extensions=['meta'])
            result = result.replace("{{ content }}", content)
        if file_metadata["filename"] != "index":
            Path(f"{self.site_dir}/build/{file_metadata['filename']}/").mkdir(parents=True,exist_ok=True)
            with open(f"{self.site_dir}/build/{file_metadata['filename']}/index.html", "w") as f:
                f.write(result)
        else:
            posts = ""
            for post in self.sorted_posts:
                posts += f"<li><a href=/{post['filename']}/>{post['publish_date']} - {post['title']}</a></li>\n"
            result = result.replace("{{ posts }}", posts)
            with open(f"{self.site_dir}/build/index.html", "w") as f:
                f.write(result)

    def build_post(self,file_metadata):
        result = ""
        with open(f"{self.site_dir}/templates/layout.html") as f:
            result = f.read()
        result = result.replace("{{ site_name }}", self.site_name)
        template = self.read_template(file_metadata["template"])
        result = result.replace("{{ template }}",template)
        tag_list = ""
        if file_metadata["tags"]:
            for tag in file_metadata["tags"]:
                tag_list += f"<a href='/tag/{tag}/'>{tag}</a>, "
            tag_list = tag_list.strip()[:-1]
        else:
            tag_list = "no tags"
        result = result.replace("{{ tags }}", tag_list)
        result = result.replace("{{ publish_date }}",file_metadata["publish_date"])
        result = result.replace("{{ title }}", f"{file_metadata['title']} - {self.site_name}")
        prev = ""
        if file_metadata["index"] != len(self.sorted_posts)-1:
            i = file_metadata["index"] + 1
            prev_filename = self.sorted_posts[i]["filename"]
            prev_title = self.sorted_posts[i]["title"]
            prev = f"<div class='prev-post'>Previous: <a href='/{prev_filename}/'>{prev_title}</a></div>"
        result = result.replace("{{ prev }}", prev)
        next = ""
        if file_metadata["index"] != 0:
            i = file_metadata["index"] - 1
            next_filename = self.sorted_posts[i]["filename"]
            next_title = self.sorted_posts[i]["title"]
            next = f"<div class='next-post'>Next: <a href='/{next_filename}/'>{next_title}</a></div>"
        result = result.replace("{{ next }}", next)
        with open(f"{self.site_dir}/content/{file_metadata['filename']}.md") as f:
            content = markdown.markdown(f.read(),extensions=['meta'])
            result = result.replace("{{ content }}", content)
        Path(f"{self.site_dir}/build/{file_metadata['filename']}/").mkdir(parents=True,exist_ok=True)
        with open(f"{self.site_dir}/build/{file_metadata['filename']}/index.html", "w") as f:
            f.write(result)

    def build_archive(self):
        result = ""
        with open(f"{self.site_dir}/templates/layout.html") as f:
            result = f.read()
        result = result.replace("{{ site_name }}", self.site_name)
        with open(f"{self.site_dir}/templates/archive.html") as f:
            template = f.read()
            result = result.replace("{{ template }}", template)
        result = result.replace("{{ title }}", f"Archive - {self.site_name}")
        posts = ""
        for post in self.sorted_posts:
            posts += f"<li><a href=/{post['filename']}/>{post['publish_date']} - {post['title']}</a></li>\n"
        result = result.replace("{{ posts }}", posts)
        Path(f"{self.site_dir}/build/archive/").mkdir(parents=True,exist_ok=True)
        with open(f"{self.site_dir}/build/archive/index.html", "w") as f:
            f.write(result)

    def build_tag_archive(self):
        tag_list = ""
        sorted_tags = sorted(self.tags)
        for tag in sorted_tags:
            tag_list += f"<li><a href='/tag/{tag}/'>{tag}</a></li>\n"
        result = ""
        with open(f"{self.site_dir}/templates/layout.html") as f:
            result = f.read()
        result = result.replace("{{ site_name }}", self.site_name)
        with open(f"{self.site_dir}/templates/tag_archive.html") as f:
            template = f.read()
            result = result.replace("{{ template }}", template)
        result = result.replace("{{ title }}", f"Tags - {self.site_name}")
        result = result.replace("{{ tags }}", tag_list)
        Path(f"{self.site_dir}/build/tags/").mkdir(parents=True,exist_ok=True)
        with open(f"{self.site_dir}/build/tags/index.html", "w") as f:
            f.write(result)

    def build_tag(self,tag):
        posts = ""
        for i in self.tags[tag]:
            filename = self.sorted_posts[i]["filename"]
            title = self.sorted_posts[i]["title"]
            publish_date = self.sorted_posts[i]["publish_date"]
            posts += f"<li><a href=/{filename}/>{publish_date} - {title}</a></li>\n"
        result = ""
        with open(f"{self.site_dir}/templates/layout.html") as f:
            result = f.read()
        result = result.replace("{{ site_name }}", self.site_name)
        with open(f"{self.site_dir}/templates/tagged.html") as f:
            template = f.read()
            result = result.replace("{{ template }}", template)
        result = result.replace("{{ title }}", f"Tag: {tag} - {self.site_name}")
        result = result.replace("{{ tag }}", tag)
        result = result.replace("{{ posts }}", posts)
        Path(f"{self.site_dir}/build/tag/{tag}/").mkdir(parents=True,exist_ok=True)
        with open(f"{self.site_dir}/build/tag/{tag}/index.html", "w") as f:
            f.write(result)

    def read_template(self,template_file):
        with open(f"{self.site_dir}/templates/{template_file}") as f:
            result = f.read()
        return result

class CommandLine:

    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="dssb",
            usage='''
dssb <command> [<args>]
List of commands:
    init    initialize a new site in a new folder
    build   build a site given a folder
    page    create a new generic markdown page
    post    create a new blog post markdown page
'''
        )
        parser.add_argument("command")
        args = parser.parse_args(sys.argv[1:2]) # exclude remaining args and run based on subcommand
        if not hasattr(self, args.command):
            print("[E] Command not recognized. Use either init, build, page, or post.")
            parser.print_help()
            exit(1)
        getattr(self, args.command)() # run method with same name as command

    def init(self):
        parser = argparse.ArgumentParser(
            description="initialize a new site in a new directory",
            usage='''
dssb init <site_name>
'''
        )
        parser.add_argument("site_name", help="name of new site directory to create")
        args = parser.parse_args(sys.argv[2:])
        builder = Builder()
        builder.new_site(args.site_name)
    
    def build(self):
        parser = argparse.ArgumentParser(
            description="build site",
            usage='''
dssb build [--dir <site_dir>]

site_dir    location of site folder (defaults to current folder)
'''
        )
        parser.add_argument("-d","--dir",
                            metavar="site_dir",
                            help="location of site folder (defaults to current folder)",
                            default=".")
        args = parser.parse_args(sys.argv[2:])
        path = os.path.abspath(".") if not args.dir else os.path.abspath(args.dir)
        builder = Builder()
        builder.build_site(path)
    
    def page(self):
        parser = argparse.ArgumentParser(
            description="create a new generic markdown page",
            usage='''
dssb page <page_name>

page_name   name of new page to create. Use a markdown (.md) extension.
'''
        )
        parser.add_argument("page_name", help="name of new page to create")
        args = parser.parse_args(sys.argv[2:])
        new_page = ""
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/defaults/new_page.md") as f:
            new_page = f.read()
        with open(f"{os.getcwd()}/{args.page_name}","w") as f:
            f.write(new_page)
    
    def post(self):
        parser = argparse.ArgumentParser(
            description=" create a new blog post markdown page",
            usage='''
dssb post <post_name>

post_name   name of new post to create. Use a markdown (.md) extension.
'''
        )
        parser.add_argument("post_name", help="name of new post to create")
        args = parser.parse_args(sys.argv[2:])
        new_post = ""
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/defaults/new_post.md") as f:
            new_post = f.read()
        with open(f"{os.getcwd()}/{args.post_name}","w") as f:
            f.write(new_post)

if __name__ == "__main__":
    CommandLine()