#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, ConfigParser, gpxpy, math, urllib2, subprocess, copy, getopt, datetime, errno, enum
from PIL import Image, ImageDraw, ImageFont, ImageOps

class opt_type(enum.Enum):
    Str = 1
    Int = 2
    Bool = 3

class opt_class:
    def __init__(self, attr, section = None, default = None, t = opt_type.Str, option = None, show = None):
        """
        :param attr: 读取成功后，对象cf_class中元素名称。
        :param section: 配置文件section，如果设置为None则不会扫描配置文件。
        :param default: 这个参数的默认值，如果为None的没设置这个attr会报错。
        :param t: 指定了这个参数的类型。
        :param option: 配置文件option和命令行的，如果设置为None则同attr。
        :param show: 用来显示的名称，显示的时候用，如果设置为None则同attr。
        """
        self.attr = attr
        self.section = section
        if option != None:
            self.option = option
        else:
            self.option = attr
        self.default = default
        self.t = t
        if show != None:
            self.show = show
        else:
            self.show = attr

    def convert(self, str_val):
        if self.t == opt_type.Int:
            val = int(str_val)
        elif self.t == opt_type.Bool:
            val = str_val.lower()
            if val == "yes" or val == "true":
                val = True
            elif val == "no" or val == "false":
                val = False
            else:
                raise Exception(self.show + "设置的" + str_val + "是什么鬼？")
        else:
            val = str_val
        return val

class cf_class(ConfigParser.ConfigParser):
    def __init__(self):
        self.opts_init()

        self.parse_cmd()
        self.parse_config()
        self.check_opts()
        self.show_opts()

    def __del__(self):
        if hasattr(self, 'cfp'):
            self.cfp.close()

    def opts_init(self):
        self.opts = []
        self.opts.append(opt_class("ffmpeg", "required"))
        self.opts.append(opt_class("gps_file", "required"))
        self.opts.append(opt_class("google_map_key", "required"))
        self.opts.append(opt_class("google_map_type", "required"))
        self.opts.append(opt_class("video_width", "required", t=opt_type.Int))
        self.opts.append(opt_class("video_height", "required", t=opt_type.Int))
        self.opts.append(opt_class("video_border", "required", t=opt_type.Int))

        self.opts.append(opt_class("google_map_premium", "optional", False, t=opt_type.Bool))
        self.opts.append(opt_class("output_dir", "optional", "./output/"))
        self.opts.append(opt_class("video_limit_secs", "optional", 0, t=opt_type.Int))
        self.opts.append(opt_class("line_color", "optional", "yellow"))
        self.opts.append(opt_class("point_color", "optional", "white"))
        self.opts.append(opt_class("font_color", "optional", "white"))
        self.opts.append(opt_class("video_codec", "optional", "libx264"))
        self.opts.append(opt_class("video_fps", "optional", 60, t=opt_type.Int))
        self.opts.append(opt_class("speed", "optional", 1, t=opt_type.Int, show="绘制速率"))
        self.opts.append(opt_class("hide_begin", "optional", 0, t=opt_type.Int))
        self.opts.append(opt_class("head_file", "optional", ""))
        self.opts.append(opt_class("head_size", "optional", 20, t=opt_type.Int))
        self.opts.append(opt_class("photos_dir", "optional", ""))
        self.opts.append(opt_class("photos_timezone", "optional", 8, t=opt_type.Int))
        self.opts.append(opt_class("photos_show_secs", "optional", 2, t=opt_type.Int))
        self.opts.append(opt_class("map_cache", "optional", True, t=opt_type.Bool))
        self.opts.append(opt_class("trackinfo_show_sec", "optional", 2, t=opt_type.Int))

    def check_opts(self):
        if self.google_map_type != "roadmap" and self.google_map_type != "satellite" and self.google_map_type != "terrain" and self.google_map_type != "hybrid":
            raise Exception("地图类型"+self.google_map_type+"是什么鬼？")

        if os.path.exists(self.output_dir) and not os.path.isdir(self.output_dir):
            raise Exception("输出目录"+self.output_dir+"不是目录，不好好设置信不信给你删了？")
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

    def parse_cmd(self):
        longopts = []
        for opt in self.opts:
            longopts.append(opt.option + "=")
        cmd_opts, config_file_path = getopt.getopt(sys.argv[1:], "", longopts)

        for arg, val in cmd_opts:
            for opt in self.opts:
                if "--" + opt.option == arg:
                    setattr(self, opt.attr, opt.convert(val))
                    break

        if len(config_file_path) == 0:
            self.config_file_path = "./config.ini"
        else:
            self.config_file_path = config_file_path[0]

    def parse_config(self):
        print "配置文件为:", self.config_file_path
        self.cfp = open(self.config_file_path)
        ConfigParser.ConfigParser.__init__(self)
        ConfigParser.ConfigParser.readfp(self, self.cfp)

        for opt in self.opts:
            if not hasattr(self, opt.attr):
                setattr(self, opt.attr, self.get_opt(opt))

    def show_opts(self):
        for opt in self.opts:
            print ("%s设置为: %s") % (opt.show, str(getattr(self, opt.attr)))

    def has_option(self, opt):
        if not ConfigParser.ConfigParser.has_option(self, opt.section, opt.option):
            return False
        if ConfigParser.ConfigParser.get(self, opt.section, opt.option) == "":
            return False
        return True

    def get_opt(self, opt):
        if not self.has_option(opt):
            if opt.default == None:
                raise Exception(opt.section+"中的项目"+opt.option+"没设置啊！")
            else:
                return opt.default
        val = ConfigParser.ConfigParser.get(self, opt.section, opt.option)
        return opt.convert(val)

class gps_class:
    def __init__(self, cf):
        self.cf = cf
        self.gfp = open(cf.gps_file)
        self.rec = gpxpy.parse(self.gfp)
        self.get_max_min_count_begin_end()

    def __del__(self):
        if hasattr(self, 'gfp'):
            self.gfp.close()

    def get_distance(self, p1, p2):
        if p1 == None or p2 == None:
            return 0

        distance = p2.distance_3d(p1)
        if not distance:
            distance = p2.distance_2d(p1)
        return distance

    def get_max_min_count_begin_end(self):
        self.max_latitude = None
        self.min_latitude = None
        self.max_longitude = None
        self.min_longitude = None
        self.count = 0
        self.begin = None
        self.end = None
        for track in self.rec.tracks:
            for segment in track.segments:
                prev_point = None
                distance = 0
                for point in segment.points:
                    if prev_point != None:
                        distance += self.get_distance(prev_point, point)
                    prev_point = point
                    if distance < self.cf.hide_begin:
                        continue

                    if self.begin == None:
                        self.begin = point
                    self.end = point
                    self.count += 1
                    if self.max_latitude == None or point.latitude > self.max_latitude:
                        self.max_latitude = point.latitude
                    if self.min_latitude == None or point.latitude < self.min_latitude:
                        self.min_latitude = point.latitude
                    if self.max_longitude == None or point.longitude > self.max_longitude:
                        self.max_longitude = point.longitude
                    if self.min_longitude == None or point.longitude < self.min_longitude:
                        self.min_longitude = point.longitude

    def track_walk(self, c):
        for track in self.rec.tracks:
            for segment in track.segments:
                for point in segment.points:
                    c.track_walk_callback(point)

class map_class:
    def __init__(self, cf, gps, photos):
        self.cbk = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728, 268435456, 536870912, 1073741824, 2147483648, 4294967296, 8589934592, 17179869184, 34359738368, 68719476736, 137438953472]
        self.cek = [0.7111111111111111, 1.4222222222222223, 2.8444444444444446, 5.688888888888889, 11.377777777777778, 22.755555555555556, 45.51111111111111, 91.02222222222223, 182.04444444444445, 364.0888888888889, 728.1777777777778, 1456.3555555555556, 2912.711111111111, 5825.422222222222, 11650.844444444445, 23301.68888888889, 46603.37777777778, 93206.75555555556, 186413.51111111112, 372827.02222222224, 745654.0444444445, 1491308.088888889, 2982616.177777778, 5965232.355555556, 11930464.711111112, 23860929.422222223, 47721858.844444446, 95443717.68888889, 190887435.37777779, 381774870.75555557, 763549741.5111111]
        self.cfk = [40.74366543152521, 81.48733086305042, 162.97466172610083, 325.94932345220167, 651.8986469044033, 1303.7972938088067, 2607.5945876176133, 5215.189175235227, 10430.378350470453, 20860.756700940907, 41721.51340188181, 83443.02680376363, 166886.05360752725, 333772.1072150545, 667544.214430109, 1335088.428860218, 2670176.857720436, 5340353.715440872, 10680707.430881744, 21361414.86176349, 42722829.72352698, 85445659.44705395, 170891318.8941079, 341782637.7882158, 683565275.5764316, 1367130551.1528633, 2734261102.3057265, 5468522204.611453, 10937044409.222906, 21874088818.445812, 43748177636.891624]

        self.gps = gps
        self.cf = cf
        self.photos = photos

        self.prev_x = None
        self.prev_y = None
        self.prev_point = None
        self.distance = 0.0
        self.img = None
        self.first_point = None
        self.not_write_distance = 0.0
        self.not_write_secs = 0
        self.current_speed = ""
        self.frame_count = 0

        if cf.google_map_premium:
            self.size_max = 2048
        else:
            self.size_max = 640

        if self.cf.video_width > self.size_max:
            raise Exception("你把video_width设置这么大不怕系统爆炸吗？")
        if self.cf.video_height > self.size_max:
            raise Exception("你把video_height设置这么大不怕系统爆炸吗？")
        b_tmp = self.cf.video_border * 2
        if b_tmp >= self.cf.video_width or b_tmp >= self.cf.video_height:
            raise Exception("你把video_border设置这么大不怕系统爆炸吗？")

        self.get_zoom_and_center(self.cf.video_width - b_tmp, self.cf.video_height - b_tmp)
        print "缩放率是", self.zoom

        self.get_font()

    #下面这两个函数取自 https://github.com/whit537/gheat/blob/master/__/lib/python/gmerc.py
    def gps_to_global_pixel(self, latitude, longitude):
        cbk = self.cbk[self.zoom]
        x = round(cbk + (longitude * self.cek[self.zoom]))
        foo = math.sin(latitude * math.pi / 180)
        if foo < -0.9999:
            foo = -0.9999
        elif foo > 0.9999:
            foo = 0.9999
        y = round(cbk + (0.5 * math.log((1+foo)/(1-foo)) * (-self.cfk[self.zoom])))

        return x, y

    def global_pixel_to_gps(self, x, y):
        foo = self.cbk[self.zoom]
        longitude = (x - foo) / self.cek[self.zoom]
        bar = (y - foo) / -self.cfk[self.zoom]
        blam = 2 * math.atan(math.exp(bar)) - math.pi / 2
        latitude = blam / (math.pi / 180)

        return latitude, longitude

    def get_zoom_and_center(self, width, height):
        for self.zoom in range(19, -1, -1):
            min_x, max_y = self.gps_to_global_pixel(self.gps.min_latitude, self.gps.min_longitude)
            max_x, min_y = self.gps_to_global_pixel(self.gps.max_latitude, self.gps.max_longitude)
            if max_x - min_x < width and max_y - min_y < height:
                break

        self.center_gx = min_x + float(max_x - min_x) / 2
        self.center_gy = min_y + float(max_y - min_y) / 2
        self.center_latitude, self.center_longitude = self.global_pixel_to_gps(self.center_gx, self.center_gy)
        self.center_x = float(self.cf.video_width - 1) / 2
        self.center_y = float(self.cf.video_height - 1) / 2

        self.max_font_height = (self.cf.video_height - (max_y - min_y))/2

    def get_font(self):
        for size in range(1, self.size_max):
            font = ImageFont.truetype('./DroidSansFallback.ttf', size = size)
            width, height = font.getsize(u'距离:999.99公里 时间:23小时59分59秒 当前速度:23小时59分59秒/公里')
            if width >= self.cf.video_width or height >= self.max_font_height:
                break
        if size != 1:
            size -= 1
        print "字体大小是", size
        self.font = ImageFont.truetype('./DroidSansFallback.ttf', size = size)

    def gps_to_pixel(self, latitude, longitude):
        gx, gy = self.gps_to_global_pixel(latitude, longitude)
        x = int(round(gx - self.center_gx + self.center_x))
        y = int(round(gy - self.center_gy + self.center_y))
        return x, y

    def remove(self, f):
        try:
            os.remove(f)
        except OSError, (error, message):
            if error != errno.ENOENT:
                raise OSError, (error, message)

    def get_map(self):
        url = "https://maps.googleapis.com/maps/api/staticmap?format=png"
        url += "&center=" + str(self.center_latitude) + "," + str(self.center_longitude)
        url += "&zoom=" + str(self.zoom)
        url += "&size=" + str(self.cf.video_width) + "x" + str(self.cf.video_height)
        url += "&maptype=" + self.cf.google_map_type
        current_url = url
        url += "&key=" + self.cf.google_map_key
        print "将从下面的地址下载地图："
        print url

        pic_file = os.path.join(self.cf.output_dir, "base.png")
        url_file = os.path.join(self.cf.output_dir, "base.url")

        if self.cf.map_cache:
            self.img = None
            try:
                if open(url_file, "r").read() == current_url:
                    self.img = Image.open(pic_file).convert("RGBA")
                    self.draw = ImageDraw.Draw(self.img)
            except:
                self.img = None
            if self.img != None:
                print "直接使用之前的地图文件。"
                return

        self.remove(pic_file)
        self.remove(url_file)

        ufp = urllib2.urlopen(url = url, timeout = 10)
        fp = open(pic_file, "wb")
        fp.write(ufp.read())
        fp.close()
        ufp.close()

        self.img = Image.open(pic_file).convert("RGBA")
        self.draw = ImageDraw.Draw(self.img)

        if self.cf.map_cache:
            fp = open(url_file, "w")
            fp.write(current_url)
            fp.close()

    def get_secs(self, p1, p2):
        if p1 == None or p2 == None:
            return 0

        return p2.time_difference(p1)

    def inc_distance(self, p1, p2):
        if p1 == None or p2 == None:
            return
        
        self.distance += self.gps.get_distance(p1, p2)

    def get_time_unicode(self, secs):
        hours = secs / (60 * 60)
        secs = secs % (60 * 60)
        mins = secs / 60
        secs = secs % 60

        ret = u""
        if hours != 0:
            ret += unicode(hours) + u"小时"
        if mins != 0:
            ret += unicode(format(mins, '02')) + u"分"
        ret += unicode(format(secs, '02')) + u"秒"

        return ret

    def get_speed_unicode(self, secs, meters):
        secs = int(secs/(meters/1000))

        ret = u""
        ret += self.get_time_unicode(secs)
        ret += u"/公里"

        return ret

    def get_move_info(self, point):
        if point != None:
            real_point = point
        else:
            real_point = self.prev_point

        ret = u""
        ret += u" 距离:" + unicode(format(self.distance/1000, '.2f'))+u"公里"
        ret += u" 时间:" + self.get_time_unicode(self.get_secs(self.first_point, real_point))
        if point != None:
            if self.frame_count == self.cf.video_fps:
                self.current_speed = u" 当前速度:" + self.get_speed_unicode(self.not_write_secs, self.not_write_distance)
                self.not_write_secs = 0
                self.not_write_distance = 0.0
                self.frame_count = 0
            ret += self.current_speed
        else:
            ret += u" 平均速度:" + self.get_speed_unicode(self.get_secs(self.first_point, real_point), self.distance)

        return ret

    def write_one_point(self, pipe, write = True, point = None):
        if self.first_point == None:
            self.first_point = point

        if point != None:
            x, y = self.gps_to_pixel(point.latitude, point.longitude)
        else:
            x, y = self.prev_x, self.prev_y

        self.inc_distance(self.prev_point, point)
        if self.distance >= self.cf.hide_begin:
            self.not_write_distance += self.gps.get_distance(self.prev_point, point)
            self.not_write_secs += self.get_secs(self.prev_point, point)
            if write:
                self.frame_count += 1

            if self.prev_x != None and point != None:
                self.draw.line([(self.prev_x, self.prev_y), (x, y)],
                               fill = self.cf.line_color, width = 3)
                if self.photos.photos_paste(pipe, self.prev_point, point):
                    self.photos.cameras_xy_add(self.prev_x, self.prev_y, x, y)
                self.photos.cameras_paste(self.img)
            if write:
                img = copy.deepcopy(self.img)
                draw = ImageDraw.Draw(img)
                draw.text((0,0),
                          self.get_move_info(point),
                          font = self.font,
                          fill = self.cf.font_color)
                if self.photos.head == None:
                    draw.ellipse([(x - 5, y - 5), (x + 5, y + 5)],
                                 fill = self.cf.point_color)
                else:
                    head_offset = self.cf.head_size / 2
                    img.paste(self.photos.head, box = (x - head_offset, y - head_offset), mask = self.photos.head_alpha)
                img.save(pipe.stdin, 'PNG')
                del(draw)
                del(img)

        if point != None:
            self.prev_x = x
            self.prev_y = y
            self.prev_point = point

class photos_class:
    def __init__(self, cf, gps):
        self.cf = cf
        self.gps = gps

        if self.cf.head_file != "":
            #头像初始化 self.head self.head_alpha
            size = (self.cf.head_size, self.cf.head_size)
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            im = Image.open(self.cf.head_file)
            self.head = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
            self.head.putalpha(mask)
            _, _, _, self.head_alpha = self.head.split()
        else:
            self.head = None

        self.photos = []
        if self.cf.photos_dir != "":
            if not os.path.exists(self.cf.photos_dir):
                raise Exception(self.cf.photos_dir + "这个目录并不存在啊！")
            if os.path.isdir(self.cf.photos_dir):
                for photo in os.listdir(self.cf.photos_dir):
                    self.photos_append(os.path.join(self.cf.photos_dir, photo))
                self.photos.sort()
            else:
                self.photos_append(self.cf.photos_dir)

        #Init camera
        if len(self.photos) > 0:
            self.camera = Image.open("./camera.png").convert("RGBA").resize((20,20),Image.ANTIALIAS)
            _, _, _, self.camera_alpha = self.camera.split()
        self.cameras_xy = []

    def photos_append(self, photo):
        try:
            d = datetime.datetime.strptime(Image.open(photo)._getexif()[36867], "%Y:%m:%d %H:%M:%S")
            d -= datetime.timedelta(hours = self.cf.photos_timezone)
        except Exception as e:
            print "读取文件" + photo + "出错：", e
            print "此文件被跳过。"
            return
        if d < self.gps.begin.time or d > self.gps.begin.time:
            print "文件" + photo + "不在轨迹范围内"
            print "此文件被跳过。"
        else:
            self.photos.append((d, photo))

    def photos_paste(self, pipe, prev_point, point):
        show_camera = False

        while len(self.photos) != 0:
            (d, photo) = self.photos[0]
            if d < prev_point.time:
                self.photos.pop(0)
                continue
            if d > point.time:
                return show_camera
            print "插入图片:", photo
            image = Image.open(photo).convert("RGBA")
            image = image.resize(self.get_fit_size(image.size), Image.ANTIALIAS)
            x_expand = (self.cf.video_width - image.size[0]) / 2
            y_expand = (self.cf.video_height - image.size[1]) / 2
            image = ImageOps.expand(image, (x_expand,y_expand,x_expand,y_expand), fill="white")
            for i in range(self.cf.video_fps * self.cf.photos_show_secs):
                image.save(pipe.stdin, 'PNG')
            self.photos.pop(0)
            show_camera = True

        return show_camera

    def cameras_xy_add(self, prev_x, prev_y, x, y):
        middle_x = (max(prev_x, x) - min(prev_x, x)) / 2 + min(prev_x, x)
        middle_y = (max(prev_y, y) - min(prev_y, y)) / 2 + min(prev_y, y)
        x_offset = self.camera.size[0] / 2
        y_offset = self.camera.size[1] / 2
        x = middle_x - x_offset
        y = middle_y - y_offset
        self.cameras_xy.append((x, y))

    def cameras_paste(self, image):
        for box in self.cameras_xy:
            image.paste(self.camera, box = box, mask = self.camera_alpha)

    def get_fit_size(self, size):
        x = float(size[0])
        y = float(size[1])

        #Try x
        if x > self.cf.video_width:
            new_x = self.cf.video_width
            new_y = new_x / x * y
        else:
            new_x = x
            new_y = y
        if new_y <= self.cf.video_height:
            return (int(new_x), int(new_y))

        #Try y
        if y > self.cf.video_height:
            new_y = self.cf.video_height
            new_x = new_y / y * x
        else:
            new_y = y
            new_x = x
        return (int(new_x), int(new_y))

class video_class:
    def __init__(self, cf, gps, m, photos):
        self.cf = cf
        self.gps = gps
        self.m = m
        self.photos = photos

        self.handle_video_limit_secs()

        self.video_file = os.path.join(cf.output_dir, 'v.mp4')
        self.ffmpeg_cmd = [cf.ffmpeg,
                           '-f', 'image2pipe',
                           '-vcodec', 'png',
                           '-r', str(self.cf.video_fps),  # FPS
                           '-i', '-',  # Indicated input comes from pipe 
                           '-q:v', '1',
                           '-c:v', self.cf.video_codec,
                           '-pix_fmt', 'yuv420p',
                           '-y', #Overwrite old file
                           self.video_file]

    def get_video_secs(self):
        pic_count = (self.gps.count - 1) / self.cf.speed
        secs = pic_count / self.cf.video_fps
        if pic_count % self.cf.video_fps > 0:
            secs += 1
        secs += len(self.photos.photos) * self.cf.photos_show_secs
        secs += self.cf.trackinfo_show_sec
        return secs

    def handle_video_limit_secs(self):
        if self.cf.video_limit_secs == 0 or self.get_video_secs() <= self.cf.video_limit_secs:
            return

        if self.cf.video_limit_secs <= len(self.photos.photos) * self.cf.photos_show_secs + self.cf.trackinfo_show_sec:
            if self.cf.photos_show_secs > 1:
                self.cf.photos_show_secs = 1
                print "选项photos_show_secs设置为1"
            if self.cf.video_limit_secs <= len(self.photos.photos) * self.cf.photos_show_secs + self.cf.trackinfo_show_sec:
                    if self.cf.trackinfo_show_sec > 1:
                        self.cf.trackinfo_show_sec = 1
                        print "选项trackinfo_show_sec设置为1"
                        if self.cf.video_limit_secs <= len(self.photos.photos) * self.cf.photos_show_secs + self.cf.trackinfo_show_sec:
                            raise Exception("video_limit_secs设置的太小，加入的图片又太多 ，支持不了！")

        if self.get_video_secs() <= self.cf.video_limit_secs:
            return

        if self.cf.video_fps < 60:
            self.cf.video_fps = 60
            print "选项video_fps设置为60"

        if self.get_video_secs() <= self.cf.video_limit_secs:
            return

        track_secs = self.cf.video_limit_secs - len(self.photos.photos) * self.cf.photos_show_secs - self.cf.trackinfo_show_sec
        pic_show_count = track_secs * self.cf.video_fps
        self.cf.speed = (self.gps.count - 1) / pic_show_count
        if (self.gps.count - 1) % pic_show_count > 0:
            self.cf.speed += 1
        print "选项speed设置为",self.cf.speed

    def write_one_point(self, point):
        self.m.write_one_point(self.pipe, self.point_count % self.cf.speed == 0, point)
        self.point_count += 1

    def generate(self):
        self.pipe = subprocess.Popen(self.ffmpeg_cmd, stdin=subprocess.PIPE)
        self.point_count = 0
        self.track_walk_callback = self.write_one_point
        self.gps.track_walk(self)
        #全部输出结束后停留2秒
        for i in range(self.cf.video_fps * self.cf.trackinfo_show_sec):
            self.m.write_one_point(self.pipe)
        self.pipe.stdin.close()
        self.pipe.wait()
        print "视频生成成功：", self.video_file

def usage():
    print "Usage:",sys.argv[0], "[options]", "[./config.ini]"
    print "       [options]和[./config.ini]信息见example.ini"

def gps2video():
    #配置对象cf初始化
    try:
        cf = cf_class()
    except getopt.GetoptError as e:
        print "命令行出错：", e
        usage()
        return
    except Exception as e:
        print "读取配置信息出错：", e
        usage()
        return

    #轨迹对象gps初始化
    gps = gps_class(cf)

    #照片类初始化
    photos = photos_class(cf, gps)

    #地图对象map初始化
    m = map_class(cf, gps, photos)

    #下载地图
    m.get_map()

    #视频类初始化
    video = video_class(cf, gps, m, photos)

    #视频生成
    video.generate()

if __name__ == "__main__":
    gps2video()
