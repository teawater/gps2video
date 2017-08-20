#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, ConfigParser, gpxpy, math, urllib2, subprocess, copy
from PIL import Image, ImageDraw, ImageFont

class gps2video_cf(ConfigParser.ConfigParser):
    def __init__(self, config_file_path):
        self.cfp = open(config_file_path)
        ConfigParser.ConfigParser.__init__(self)
        ConfigParser.ConfigParser.readfp(self, self.cfp)

        self.ffmpeg = self.get("required", "ffmpeg")
        print ("ffmpeg设置为: %s") % self.ffmpeg

        self.gps_file = self.get("required", "gps_file")
        print ("gps_file设置为: %s") % self.gps_file

        self.google_map_key = self.get("required", "google_map_key")
        print ("google_map_key设置为: %s") % self.google_map_key

        self.google_map_type = self.get("required", "google_map_type")
        if self.google_map_type != "roadmap" and self.google_map_type != "satellite" and self.google_map_type != "terrain" and self.google_map_type != "hybrid":
            raise Exception("地图类型"+self.google_map_type+"是什么鬼？")
        print ("google_map_type设置为: %s") % self.google_map_type

        self.video_width = self.getint("required", "video_width")
        print ("video_width设置为: %d") % self.video_width

        self.video_height = self.getint("required", "video_height")
        print ("video_height设置为: %d") % self.video_height

        self.video_border = self.getint("required", "video_border")
        print ("video_border设置为: %d") % self.video_border

        self.google_map_premium = self.get("optional", "google_map_premium", "no")
        if self.google_map_premium == "yes":
            self.google_map_premium = True
        elif self.google_map_premium == "no":
            self.google_map_premium = False
        else:
            raise Exception("你到底是不是google map premium，写清楚！")
        print "google_map_premium 设置为:", self.google_map_premium

        self.output_dir = self.get("optional", "output_dir", "./output/")
        if os.path.exists(self.output_dir) and not os.path.isdir(self.output_dir):
            raise Exception("输出目录"+self.output_dir+"不是目录，不好好设置信不信给你删了？")
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        print ("输出目录设置为: %s") % self.output_dir

        self.line_color = self.get("optional", "line_color", "yellow")
        print ("line_color设置为: %s") % self.line_color

        self.point_color = self.get("optional", "point_color", "white")
        print ("point_color设置为: %s") % self.point_color

        self.font_color = self.get("optional", "font_color", "white")
        print ("font_color设置为: %s") % self.font_color

        self.speed = self.getint("optional", "speed", 1)
        print ("绘制速率为: %dx") % self.speed

    def __del__(self):
        if hasattr(self, 'cfp'):
            self.cfp.close()

    def has_option(self, section, option):
        if not ConfigParser.ConfigParser.has_option(self, section, option):
            return False
        if ConfigParser.ConfigParser.get(self, section, option) == "":
            return False
        return True

    def get(self, section, option, default = None):
        if not self.has_option(section, option):
            if default == None:
                raise Exception(section+"中的项目"+option+"没设置啊！")
            else:
                return default
        return ConfigParser.ConfigParser.get(self, section, option)

    def getint(self, section, option, default = None):
        if not self.has_option(section, option):
            if default == None:
                raise Exception(section+"中的项目"+option+"没设置啊！")
            else:
                return default
        return ConfigParser.ConfigParser.getint(self, section, option)

class gps_class:
    def __init__(self, cf):
        self.cf = cf
        self.gfp = open(cf.gps_file)
        self.rec = gpxpy.parse(self.gfp)
        self.get_max_min()

    def __del__(self):
        if hasattr(self, 'gfp'):
            self.gfp.close()

    def get_max_min(self):
        self.max_latitude = None
        self.min_latitude = None
        self.max_longitude = None
        self.min_longitude = None
        for track in self.rec.tracks:
            for segment in track.segments:
                for point in segment.points:
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
    def __init__(self, cf, gps):
        self.cbk = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728, 268435456, 536870912, 1073741824, 2147483648, 4294967296, 8589934592, 17179869184, 34359738368, 68719476736, 137438953472]
        self.cek = [0.7111111111111111, 1.4222222222222223, 2.8444444444444446, 5.688888888888889, 11.377777777777778, 22.755555555555556, 45.51111111111111, 91.02222222222223, 182.04444444444445, 364.0888888888889, 728.1777777777778, 1456.3555555555556, 2912.711111111111, 5825.422222222222, 11650.844444444445, 23301.68888888889, 46603.37777777778, 93206.75555555556, 186413.51111111112, 372827.02222222224, 745654.0444444445, 1491308.088888889, 2982616.177777778, 5965232.355555556, 11930464.711111112, 23860929.422222223, 47721858.844444446, 95443717.68888889, 190887435.37777779, 381774870.75555557, 763549741.5111111]
        self.cfk = [40.74366543152521, 81.48733086305042, 162.97466172610083, 325.94932345220167, 651.8986469044033, 1303.7972938088067, 2607.5945876176133, 5215.189175235227, 10430.378350470453, 20860.756700940907, 41721.51340188181, 83443.02680376363, 166886.05360752725, 333772.1072150545, 667544.214430109, 1335088.428860218, 2670176.857720436, 5340353.715440872, 10680707.430881744, 21361414.86176349, 42722829.72352698, 85445659.44705395, 170891318.8941079, 341782637.7882158, 683565275.5764316, 1367130551.1528633, 2734261102.3057265, 5468522204.611453, 10937044409.222906, 21874088818.445812, 43748177636.891624]

        self.gps = gps
        self.cf = cf
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
            width, height = font.getsize(u'距离:999.99公里 当前速度:23小时59分59秒/公里')
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

    def get_map(self):
        url = "https://maps.googleapis.com/maps/api/staticmap?format=png"
        url += "&key=" + self.cf.google_map_key
        url += "&center=" + str(self.center_latitude) + "," + str(self.center_longitude)
        url += "&zoom=" + str(self.zoom)
        url += "&size=" + str(self.cf.video_width) + "x" + str(self.cf.video_height)
        url += "&maptype=" + self.cf.google_map_type
        print "将从下面的地址下载地图："
        print url

        self.pic = os.path.join(self.cf.output_dir, "base.png")

        ufp = urllib2.urlopen(url = url, timeout = 10)
        fp = open(self.pic, "wb")
        fp.write(ufp.read())
        fp.close()
        ufp.close()

        self.img = Image.open(self.pic)
        self.img = self.img.convert("RGBA")
        self.draw = ImageDraw.Draw(self.img)

    def get_secs(self, p1, p2):
        if p1 == None or p2 == None:
            return 0

        return p2.time_difference(p1)

    def get_distance(self, p1, p2):
        if p1 == None or p2 == None:
            return 0

        distance = p2.distance_3d(p1)
        if not distance:
            distance = p2.distance_2d(p1)
        return distance

    def inc_distance(self, p1, p2):
        if p1 == None or p2 == None:
            return
        
        self.distance += self.get_distance(p1, p2)

    def get_speed_unicode(self, secs, meters):
        secs = int(secs/(meters/1000))

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

    def get_move_info(self, current):
        ret = u""

        ret += u" 距离:" + unicode(format(self.distance/1000, '.2f'))+u"公里"
        if current:
            if self.frame_count == 32:
                self.current_speed = u" 当前速度:" + self.get_speed_unicode(self.not_write_secs, self.not_write_distance)
                self.not_write_secs = 0
                self.not_write_distance = 0.0
                self.frame_count = 0
            ret += self.current_speed
        else:
            ret += u" 平均速度:" + self.get_speed_unicode(self.get_secs(self.first_point, self.prev_point), self.distance)

        return ret

    def write_one_point(self, pipe, write = True, point = None):
        if self.first_point == None:
            self.first_point = point

        self.inc_distance(self.prev_point, point)
        self.not_write_distance += self.get_distance(self.prev_point, point)
        self.not_write_secs += self.get_secs(self.prev_point, point)
        if write:
            self.frame_count += 1

        if point != None:
            x, y = self.gps_to_pixel(point.latitude, point.longitude)
        else:
            x, y = self.prev_x, self.prev_y
        if self.prev_x != None and point != None:
            self.draw.line([(self.prev_x, self.prev_y), (x, y)],
                           fill = self.cf.line_color, width = 3)
        if write:
            img = copy.deepcopy(self.img)
            draw = ImageDraw.Draw(img)
            draw.ellipse([(x - 5, y - 5), (x + 5, y + 5)],
                         fill = self.cf.point_color)
            draw.text((0,0),
                      self.get_move_info(point != None),
                      font = self.font,
                      fill = self.cf.font_color)
            img.save(pipe.stdin, 'PNG')
            del(draw)
            del(img)

        if point != None:
            self.prev_x = x
            self.prev_y = y
            self.prev_point = point

class video_class:
    def __init__(self, cf):
        self.cf = cf

        self.video_file = os.path.join(cf.output_dir, 'v.mp4')
        self.ffmpeg_cmd = [cf.ffmpeg,
                           '-f', 'image2pipe',
                           '-vcodec', 'png',
                           '-r', '36',  # FPS
                           '-i', '-',  # Indicated input comes from pipe 
                           '-q:v', '1',
                           '-c:v', 'mpeg4',
                           '-y', #Overwrite old file
                           self.video_file]

    def write_one_point(self, point):
        self.m.write_one_point(self.pipe, self.point_count % self.cf.speed == 0, point)
        self.point_count += 1

    def generate(self, m, gps):
        self.m = m
        self.pipe = subprocess.Popen(self.ffmpeg_cmd, stdin=subprocess.PIPE)
        self.point_count = 0
        self.track_walk_callback = self.write_one_point
        gps.track_walk(self)
        #全部输出结束后停留2秒
        for i in range(36 * 2):
            m.write_one_point(self.pipe)
        self.pipe.stdin.close()
        self.pipe.wait()
        print "视频生成成功：", self.video_file

def gps2video(config_file_path="config.ini"):
    #配置对象cf初始化
    try:
        cf = gps2video_cf(config_file_path)
    except Exception as e:
        print config_file_path + "文件打开出错：", e
        print "打开example.ini文件，对里面的配置信息进行修改后另存为"+config_file_path+"。"
        print "不用担心不会配置，里面有中文注释。"
        return

    #轨迹对象gps初始化
    gps = gps_class(cf)

    #地图对象map初始化
    m = map_class(cf, gps)

    #下载地图
    m.get_map()

    #视频类初始化
    video = video_class(cf)

    #视频生成
    video.generate(m, gps)

if __name__ == "__main__":
    gps2video()
