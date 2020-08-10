import os
import sys
import glob
import exifread
from os.path import isfile, join
from os import listdir, path, remove
from PIL import Image, ImageDraw, ImageFont, ImageFilter


PICTURE_FOLDER = ""
PREPROCESS_FLAG = "_2000."
MY_SPECIAL_TAG = "_lcy"
ADDITIONAL_OUTPUT_FOLDER = "_frame"

OPTION_CLEAR_PICTURES = 0

RESIZE_WIDTH_LANDSCAPE = 900
RESIZE_WIDTH_PORTRAIT = 500

def draw_frame(ctx, x, y, width, height, color, line_width):
    offset = 2
    ctx.line((x-offset, y, x+width+offset, y), color, line_width)
    ctx.line((x+width, y, x+width, y+height), color, line_width+1)
    ctx.line((x+width+offset, y+height, x-offset, y+height), color, line_width)
    ctx.line((x, y+height, x, y), color, line_width+1)

def add_frame(input_file, output_path):
    # check landscape or portrait
    img_resize = Image.open(input_file).convert("RGBA")
    origin_width, origin_height = img_resize.size
    is_landscape = (origin_width >= origin_height)

    # calculate resize's height
    resize_width = RESIZE_WIDTH_LANDSCAPE
    if is_landscape != True:
        resize_width = RESIZE_WIDTH_PORTRAIT
    wpercent = (resize_width/float(img_resize.size[0]))
    resize_height = int((float(img_resize.size[1])*float(wpercent)))

    # calculate frame size
    frame_width = (int)(resize_width * 1.13)
    frame_width += (frame_width % 2)
    frame_height = (int)(frame_width * 0.89)
    frame_height += (frame_height % 2)
    if is_landscape != True:
        frame_width = (int)(resize_width * 1.7)
        frame_width += (frame_width % 2)
        frame_height = frame_width


    # calculate picture's left/top
    left = (int)((frame_width - resize_width) / 2.0)
    top = (int)((frame_height - resize_height) / 4.1)
    if is_landscape != True:
        left = (int)(frame_width * 0.05) 
        top = (int)((frame_height - resize_height) / 2)

    # resize picture
    img_resize = img_resize.resize((resize_width, resize_height), Image.ANTIALIAS)

    # create background image
    img_frame = Image.new('RGBA', (frame_width, frame_height), (255, 255, 255))

    # overlay picture
    img_frame.paste(img_resize, (left, top))

    # draw text
    imgexif = open(input_file, 'rb')
    exif = exifread.process_file(imgexif)
    #for key in exif.keys():
    #    print("tag: %s, value: %s" % (key, exif[key]))
    shot_time = "unkown shot time"
    date_time = ""
    if "EXIF DateTimeOriginal" in exif.keys():
        shot_time = exif["EXIF DateTimeOriginal"].printable
        date_time = shot_time.split(" ", 1)[0]
        date_time = date_time.split(":")
        date_time = ("'%s %d %d" % (date_time[0][2:4], int(date_time[1]), int(date_time[2])))
    draw_text = date_time
    # for NOMO film
    desc = ""
    if "Image ImageDescription" in exif.keys():
        desc = exif["Image ImageDescription"].printable
        idx = desc.find("NOMO")
        if desc != "" and  -1 != idx:
            desc = desc[(idx+len("NOMO ")):(len(desc)-1)]
            draw_text += ("  " + desc)
    draw_text = ("%s  %dx%d" % (draw_text, resize_width, resize_height))
    font = ImageFont.truetype('Arial.ttf', 18)
    draw = ImageDraw.Draw(img_frame)
    if is_landscape == True:
        draw.text((left, top + resize_height + 10), draw_text, font=font, fill=(230, 230, 230))
    else:
        draw.text((left+resize_width + 18, top + resize_height - 18), draw_text, font=font, fill=(230, 230, 230))

    # draw frame line
    draw_frame(draw, 0, 0, frame_width, frame_height, "black", 12)
    draw_frame(draw, left, top, resize_width, resize_height, "black", 3)

    # claculate output file path
    riginal_path, original_file_name = path.split(input_file)
    output_name, output_ext_name = path.splitext(original_file_name)
    text_time = shot_time.replace(":", "-")
    text_time = text_time.replace(" ", "_")
    output_name += ("_%dx%d_%s%s" % (frame_width, frame_height, text_time, MY_SPECIAL_TAG))
    output_name += output_ext_name
    #output_folder = ("%s/%s" % (riginal_path, ADDITIONAL_OUTPUT_FOLDER))
    output_folder = output_path
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_full_path = ("%s/%s" % (output_folder, output_name))

    # show picture used for debug
    #img_frame.show()

    # write file
    img_frame = img_frame.convert("RGB")
    img_frame.save(output_full_path, quality=100)
    #shutil.copy(output_name, additional_output_path)
    print(output_full_path)

def GetMeThePictures(mypath):
    OriginalPictures = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return OriginalPictures

def search_files(dirname):
    filter = [".jpg", ".JPG", ".jpeg", ".JPEG"]
    result = []

    for filename in os.listdir(dirname):
        apath = os.path.join(dirname, filename)
        ext = os.path.splitext(apath)[1]
        if ext in filter:
            if -1 == apath.find(MY_SPECIAL_TAG):
                if PREPROCESS_FLAG == "" or -1 != apath.find(PREPROCESS_FLAG):
                    result.append(apath)

    # serach sub-folder
    # for maindir, subdir, file_name_list in os.walk(dirname):
    #     for filename in file_name_list:
    #         apath = os.path.join(maindir, filename)#合并成一个完整路径
    #         ext = os.path.splitext(apath)[1]  # 获取文件后缀 [0]获取的是除了文件名以外的内容
    #         if ext in filter:
    #             if -1 == apath.find(MY_SPECIAL_TAG):
    #                 if PREPROCESS_FLAG == "" or -1 != apath.find(PREPROCESS_FLAG):
    #                     result.append(apath)
    return result

def usage():
	print ("""
usage: add_frame [path_of_picture][-h][-v]

arguments:
    path_of_picture	    path of JPG file
    -i                  ignore PREPROCESS_FLAG("_2000.") flag from source picture
    -c                  clear/delete all pictures on output folder before resize
    -h, --help			show this help message and exit
    -v, --version		show version information and exit
""")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("arguments error!\r\n-h shows usage.")
        #PICTURE_FOLDER = "/Users/junlin/myPhoto/from_mobile/film"
        sys.exit()
    for arg in sys.argv[1:]:
        if arg == '-v' or arg == "--version":
            print("1.0.0")
            sys.exit()
        elif arg == '-h' or arg == '--help':
            usage()
            sys.exit()
        elif arg == '-i' or arg == '--ignore':
            PREPROCESS_FLAG = ""
        elif arg == '-c' or arg == '--clear':
            OPTION_CLEAR_PICTURES = 1
    PICTURE_FOLDER = sys.argv[1]


    # search 
    files = search_files(PICTURE_FOLDER)
    if len(files) == 0:
        print("no file found. %s" % PICTURE_FOLDER)
        sys.exit()
    #print(files)
    #sys.exit()

    # create additional output folder
    full_additional_path = ("%s/%s" % (PICTURE_FOLDER, ADDITIONAL_OUTPUT_FOLDER))
    is_exist = os.path.exists(full_additional_path)
    if not is_exist:
        os.makedirs(full_additional_path)
    elif OPTION_CLEAR_PICTURES == 1:
        fileNames = glob.glob(full_additional_path + r'/*')
        for fileName in fileNames:
            os.remove(fileName)

    # Resize the Original files.
    for each_picture in files:
        add_frame(each_picture, full_additional_path)
        #break

    # print ("output folder: %s" % full_additional_path)
    print ("Done.")
