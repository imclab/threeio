import os
import json
import stat
import shutil
import argparse


os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir('..')
review = os.path.join(os.getcwd(), 'review')

MASK = stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH

HTML = '''<!doctype html>
<html>
  <head>
    <title>%(title)s</title>
    <meta charset='utf-8'>
    <meta name='review' content='width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0'>
    <script src='../scripts/three.js'></script>
    <script src='../scripts/OrbitControls.js'></script>
    <script src='../../../js/threeio.js'></script>
    <script src='../scripts/review.js'></script>
    <link href='../scripts/style.css' rel='stylesheet' />
  </head>
  <body>
    <script>
      init('%(filename)s');
    </script>
  </body>
</html>
'''

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('test_json')
    parser.add_argument('-t', '--tag', required=True)
    return vars(parser.parse_args())


def copy_for_review(tmp_json, tag):
    tag_dir = os.path.join(review, tag)
    if not os.path.exists(tag_dir):
        print('making %s' % tag_dir)
        os.makedirs(tag_dir)
    dst_json = os.path.join(tag_dir, '%s.json' % tag)
    print('moving %s > %s' % (tmp_json, dst_json))
    shutil.move(tmp_json, dst_json)
    create_template(tag_dir, os.path.basename(dst_json))

    print('looking for maps...')
    with open(dst_json) as stream:
        data = json.load(stream)

    textures = []
    materials = data.get('materials')
    if data['metadata']['type'] == 'Geometry' and materials:
        textures.extend(_parse_geometry_materials(materials))

    images = data.get('images')
    if data['metadata']['type'] == 'Object' and images:
        for each in images:
            textures.append(each['url'])
    
    textures = list(set(textures))
    print('found %d maps' % len(textures))
    dir_tmp = os.path.dirname(tmp_json)
    for texture in textures:
        texture = os.path.join(dir_tmp, texture)
        dst = os.path.join(tag_dir, os.path.basename(texture))
        shutil.move(texture, dst)
        print('moving %s > %s' % (texture, dst))

def _parse_geometry_materials(materials):
    maps = ('mapDiffuse', 'mapSpecular', 'mapBump',
        'mapLight', 'mapNormal')
    textures = []
    for material in materials:
        for key in material.keys():
            if key in maps:
                textures.append(material[key])
    return textures


def create_template(tag_dir, filename):
    html = HTML % {
        'title': filename[:-5].title(),
        'filename': filename
    }

    html_path = os.path.join(tag_dir, 'index.html')
    with open(html_path, 'w') as stream:
        stream.write(html)
    os.chmod(html_path, MASK)


def _remove_uuid(new, old):
    for key, value in old.items():
        if key == 'uuid': continue

        if isinstance(value, list):
            new[key] = []
            for val in value:
                if isinstance(val, dict):
                    new[key].append({})
                    _remove_uuid(new[key][-1], val)
                else:
                    new[key].append(val)
        elif isinstance(value, dict):
            new[key] = {}
            _remove_uuid(new[key], value)
        else:
            new[key] = value


def main():
    args = parse_args()

    if os.path.exists(args['test_json']):
        copy_for_review(args['test_json'], args['tag'])


if __name__ == '__main__':
    main()
