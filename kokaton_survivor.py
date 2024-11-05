import math
import os
import random
import sys
import time
import pygame as pg
from pygame.locals import *
import random
import math
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))



def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self, life: int):
        """
        重力場Surfaceを生成する
        引数 life：重力場の発動時間
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.set_alpha(128)  # 透明度を設定
        self.image.fill((0, 0, 0))  # 黒い矩形
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        """
        発動時間を1減算し、0未満になったら消滅する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class GravityItem(pg.sprite.Sprite):
    """
    重力場発動アイテムに関するクラス
    """
    def __init__(self, screen: pg.Surface):
        """
        重力場発動アイテムを生成する
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/bakudan.png"), 0, 0.15)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.25)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"  # 追加: 通常状態
        self.hyper_life = 0    # 追加: 発動時間

        self.skills = []  # スキルの格納リスト(手持ちのスキル)
        self.wait_skill = False  # スキル選択画面の表示について


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.25)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)
        
        screen.blit(self.image, self.rect)

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Beam(pg.sprite.Sprite):
    """
    追尾機能付きビームに関するクラス
    """
    def __init__(self, bird: Bird, xbeam: float, enemies: pg.sprite.Group, clown_enemies: pg.sprite.Group):
        """
        ビームを生成する
        引数1 bird：ビームを放つこうかとん
        引数2 xbeam：ビーム倍率
        引数3 enemies：通常の敵機グループ
        引数4 clown_enemies：ピエロの敵機グループ
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), 0, 2.0)
        self.rect = self.image.get_rect()
        self.rect.center = bird.rect.center
        self.speed = 10
        
        # 最も近い敵を特定
        self.target = self._find_nearest_enemy(bird, enemies, clown_enemies)
        # 初期の移動方向を設定
        self.vx, self.vy = bird.dire if self.target is None else calc_orientation(self.rect, self.target.rect)
        
        # 角度の計算と画像の回転
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, xbeam)

    def _find_nearest_enemy(self, bird: Bird, enemies: pg.sprite.Group, clown_enemies: pg.sprite.Group) -> pg.sprite.Sprite:
        """
        全ての敵（通常の敵とピエロ）の中から最も近い敵を見つける
        引数1 bird：こうかとん
        引数2 enemies：通常の敵機グループ
        引数3 clown_enemies：ピエロの敵機グループ
        戻り値：最も近い敵のSprite（敵がいない場合はNone）
        """
        nearest_enemy = None
        min_distance = float('inf')
        
        # 通常の敵とピエロの敵を両方チェック
        for enemy in list(enemies) + list(clown_enemies):
            distance = math.hypot(bird.rect.centerx - enemy.rect.centerx,
                                bird.rect.centery - enemy.rect.centery)
            if distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy
        
        return nearest_enemy

    def update(self, xbeam: float):
        """
        ビームを移動させる
        敵が生存している場合は追尾する
        """
        if self.target and self.target.alive():
            # ターゲットの方向を再計算
            self.vx, self.vy = calc_orientation(self.rect, self.target.rect)
            # 画像の角度を更新
            angle = math.degrees(math.atan2(-self.vy, self.vx))
            self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, xbeam)
        
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if (self.rect.centerx <= 0 or self.rect.centerx >= WIDTH) and (self.rect.centery <= 0 or self.rect.centery >= HEIGHT):
            self.kill()

class NeoBeam:
    """
    複数方向ビームに関するクラス
    """
    def __init__(self, bird: Bird, num: int):
        """
        引数1 bird：ビームを放つこうかとん
        引数2 num：ビームの数
        """
        self.bird = bird
        self.num = num
    
    def gen_beams(self, xbeam: float) -> list[Beam]:
        """
        複数方向のビームを生成する
        戻り値：Beamインスタンスのリスト
        """
        beams = []
        angle_range = 100  # -50度から+50度
        angle_step = angle_range / (self.num - 1) if self.num > 1 else 0
        
        for i in range(self.num):
            angle = -50 + (i * angle_step)  # -50度から+50度までの角度を計算
            beams.append(Beam(self.bird, xbeam, angle))
        
        return beams

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Durian(pg.sprite.Sprite):
    """
    スキル:ドリアンのこと
     
    まだ終わってないよ
    """
    def __init__(self, player: Bird):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/fruit_durian.png"), 0, 0.3)  # ドリアンの倍率設定
        self.rect = self.image.get_rect()
        self.rect.center = player.rect.center  # ドリアンの初期座標
        # self.x = player.rect.centerx  #ドリアンの初期x座標をこうかとんに設定
        # self.y = player.rect.centery  #ドリアンの初期y座標をこうかとんに設定
        self.vx = 1  # 初期速度(x方向)
        self.vy = 1  # 初期速度(y方向)
        self.speed = 3

    def update(self):
        # self.x += self.vx
        # self.y += self.vy  # 右下発射
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)

        if self.rect.left < 0:  # 左壁衝突時の反転
            # self.x = 50
            self.vx *= -1
        if self.rect.right > WIDTH:  # 右壁衝突時の反転
            # self.x = WIDTH - 50
            self.vx *= -1
        if self.rect.top < 0:  # 上壁衝突時の反転
            # self.y = 60
            self.vy *= -1
        if self.rect.bottom > HEIGHT:  # 下壁衝突時の反転
            # self.y = HEIGHT - 60
            self.vy *= -1
        

        # self.rect = self.image.get_rect()
        # self.rect.center = (self.x, self.y)

        # self.rect.center = (
        #     self.player.rect.centerx + math.cos(self.angle) * self.radius,
        #     self.player.rect.centery + math.sin(self.angle) * self.radius
        # )
        # hits = pg.sprite.spritecollide(self, emys, True)
        # for hit in hits:
        #     exps.add(Explosion(hit, 100))
        #     score.value += 8

class Soccerball(pg.sprite.Sprite):
    def __init__(self, player: Bird):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/sport_soccerball.png"), 0, 0.1)  # サッカーボールの倍率設定
        self.rect = self.image.get_rect()
        self.rect.center = player.rect.center  # サッカーボールの初期座標
        # self.x = player.rect.centerx  #サッカーボールの初期x座標をこうかとんに設定
        # self.y = player.rect.centery  #サッカーボールの初期y座標をこうかとんに設定
        self.vx = 1  # 初期速度(x方向)
        self.vy = 1  # 初期速度(y方向)
        self.speed = 10

    def update(self, emy_rct):
        # self.x -= self.vx
        # self.y -= self.vy  # 左上発射
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)

        if self.rect.left < 0 or self.rect.right > WIDTH:  # 左と右壁衝突時の反転
            # self.x = 20
            self.vx *= -1
        if self.rect.top < 0 or self.rect.bottom > HEIGHT:  # 上と下壁衝突時の反転
            # self.y = 20
            self.vy *= -1
        
        # self.rect.center = (self.x, self.y)
    
        for emy in pg.sprite.spritecollide(self, emy_rct, False):
            #balls.update(emy)
    # def hit(self, emy_rct):
            if self.rect.left <= emy.rect.right or self.rect.right >= emy.rect.left:
                self.vx *= -1
            if self.rect.top >= emy.rect.bottom or self.rect.bottom <= emy.rect.top:
                self.vy *= -1



class Enemy(pg.sprite.Sprite):
    def __init__(self, player: Bird, spawn_directions: int):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/alien1.png"), 0, 0.5)
        self.rect = self.image.get_rect()
        
        # 指定された方向数に基づいてランダムな角度を選択
        angle = random.randint(0, spawn_directions-1) * (360/spawn_directions)
        angle_rad = math.radians(angle)
        radius = max(WIDTH, HEIGHT) + 100  # 画面外からの出現を確実にする
        
        self.rect.center = (
            WIDTH/2 + math.cos(angle_rad) * radius,
            HEIGHT/2 + math.sin(angle_rad) * radius
        )
        
        self.player = player
        self.speed = 3
        self.visible = False  # 画面内に入ったかどうかのフラグ

    def update(self):
        self.vx, self.vy = calc_orientation(self.rect, self.player.rect)
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
import random
import math
import pygame as pg

class ClownEnemy(pg.sprite.Sprite):
    """ピエロの敵クラス"""
    def __init__(self, player: "Bird", spawn_directions: int):
        super().__init__()
        # 基本の画像設定
        self.image = pg.transform.rotozoom(pg.image.load("fig/images.jpg"), 0, 0.25)
        self.rect = self.image.get_rect()
        
        # 出現位置の設定（画面外から確実に出現するように修正）
        angle = random.randint(0, spawn_directions-1) * (360/spawn_directions)
        angle_rad = math.radians(angle)
        radius =max(WIDTH, HEIGHT) + 100  # 画面外からの距離を調整
        
        # 画面の中心からの位置を計算
        spawn_x = WIDTH/2 + math.cos(angle_rad) * radius
        spawn_y = HEIGHT/2 + math.sin(angle_rad) * radius
        
        # 画面外になるように調整
        if spawn_x < WIDTH/2:
            spawn_x = -50
        elif spawn_x >= WIDTH/2:
            spawn_x = WIDTH + 50
            
        if spawn_y < HEIGHT/2:
            spawn_y = -50
        elif spawn_y >= HEIGHT/2:
            spawn_y = HEIGHT + 50
            
        self.rect.center = (spawn_x, spawn_y)
        self.player = player
        self.base_speed = 2
        self.speed = self.base_speed
        self.points = 20
        
        # 移動用の変数
        self.vx = 0
        self.vy = 0
        self.movement_phase = 0

    def update(self):
        """敵の更新処理"""
        # プレイヤーへの方向を計算
        target_x = self.player.rect.centerx - self.rect.centerx
        target_y = self.player.rect.centery - self.rect.centery
        
        # 方向の正規化
        distance = math.sqrt(target_x**2 + target_y**2)
        if distance != 0:
            self.vx = (target_x / distance) * self.speed
            self.vy = (target_y / distance) * self.speed
            
        # ジグザグ動作の追加
        self.movement_phase += 0.1
        perpendicular_x = -self.vy  # 垂直方向のベクトル
        perpendicular_y = self.vx
        zigzag = math.sin(self.movement_phase) * 2  # ジグザグの振れ幅を調整
        
        # 最終的な移動を適用
        self.rect.x += self.vx + perpendicular_x * zigzag
        self.rect.y += self.vy + perpendicular_y * zigzag


class Item(pg.sprite.Sprite):
    """
    強化アイテムに関するクラス
    """
    def __init__(self, screen: pg.Surface):
        """
        強化アイテムSurfaceを生成する
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/kouseki_colorful.png"), 0, 0.1)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)
        


def main():
    pg.display.set_caption("こうかとんサバイバー")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    level_save = 0

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    cemys = pg.sprite.Group()
    gravities = pg.sprite.Group()
    items = pg.sprite.Group()
    gravityitems = pg.sprite.Group()
    # skills = pg.sprite.Group()  # スキルの格納グループの生成
    drns = pg.sprite.Group()  # ドリアンのグループ
    balls = pg.sprite.Group()  # サッカーボールのグループ

    tmr = 0
    beam_timer = 0  # 追加: ビーム発射のタイマー
    clock = pg.time.Clock()
    spawn_directions = 4  # 初期の出現方向数
    enemies_per_spawn = 3  # 初期の出現数
    last_enemy_increase = 0  # 最後に敵の数を増やした時間
    xbeam = 1.0  # 初期のビーム倍率
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            """
            スキル選択画面
            敵を倒した数で判断
            選択画面表示中はすべての時間をSTOPする
            キーボードでスキルの選択:
                1 ドリアン
                2 サッカーボール
            """
            if bird.wait_skill:  # birdで定義、スキル画面のこと
                if event.type == pg.KEYDOWN:  # キーが押されたら
                    if event.key == pg.K_1:  # 1を押したら
                        drns.add(Durian(bird))  # スキルのリストに、クラス(Durian)を追加
                        bird.wait_skill = False  # この画面を消す
                    if event.key == pg.K_2:  #2を押したら
                        balls.add(Soccerball(bird))  # スキルリストに、クラス(Soccerball)を追加
                        bird.wait_skill = False  # この画面を消す

        # 定期的に自動発射
        beam_timer += 1
        if beam_timer % 30 == 0:  # 30フレームごとにビームを自動発射
            beams.add(Beam(bird, xbeam,emys,cemys))  # emysグループを渡す
            beam_timer = 0  # タイマーをリセット

        screen.blit(bg_img, [0, 0])

        # 5秒ごとに敵の出現数と方向を増やす
        current_time = tmr // 50  # フレーム数を秒数に変換
        if current_time - last_enemy_increase >= 5:
            enemies_per_spawn += 100  # 出現数を2増やす
            spawn_directions += 2   # 方向を2増やす
            last_enemy_increase = current_time

        if tmr % 20 == 0:  # 200フレームに1回、敵機を出現させる
            emys.add(Enemy(bird, spawn_directions))

        if tmr % 100 == 0:  # 250フレームに1回、ピエロの敵機を出現させる
            cemys.add(ClownEnemy(bird, spawn_directions)) 

        if tmr != 0:
            if tmr%400 == 0:  # 400フレームに1回、強化アイテムを出現させる
                items.add(Item(screen))

        if tmr != 0:
            if tmr%1200 == 0:  # 1200フレームに1回、重力場発動アイテムを出現させる
                gravityitems.add(GravityItem(screen))

        # 通常の敵との衝突判定
        if pg.sprite.spritecollideany(bird, emys):
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        # ピエロとの衝突判定
        if pg.sprite.spritecollideany(bird, cemys):
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

            if int(score.value / 250) > level_save:  # 30点ごとにスキルの選択
                bird.wait_skill = True
                print(level_save)
                level_save = int(score.value / 250)

        for emy in pg.sprite.groupcollide(emys, drns, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 5

        for emy in pg.sprite.groupcollide(cemys, drns, True, False).keys():
            exps.add(Explosion(cemy, 100))
            score.value += 5

        balls.update(emys)  # 反射のみ
        balls.update(cemys)  # 反射のみ

        for emy in pg.sprite.groupcollide(emys, balls, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 5

        for emy in pg.sprite.groupcollide(cemys, balls, True, False).keys():
            exps.add(Explosion(cemy, 100))
            score.value += 5

        for cemy in pg.sprite.groupcollide(cemys, beams, True, True).keys():
            exps.add(Explosion(cemy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
            if int(score.value / 250) > level_save:  # 30点ごとにスキルの選択
                bird.wait_skill = True
                print(level_save)
                level_save = int(score.value / 250)
            
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, gravities, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for emy in pg.sprite.groupcollide(emys, gravities, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ

        for cemy in pg.sprite.groupcollide(cemys, gravities, True, False).keys():
            exps.add(Explosion(cemy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ

        for item in pg.sprite.spritecollide(bird, items, True):  # こうかとんと強化アイテムがぶつかったら
            xbeam += 0.2  # ビームの倍率をあげる
            if bird.speed <= 20:
                bird.speed *= 1.1 
            item.kill()  # 強化アイテムを削除する

        for gitem in pg.sprite.spritecollide(bird, gravityitems, True):  # こうかとんと重力場発動アイテムがぶつかったら
            gravities.add(Gravity(400))
            gitem.kill()  # 重力場発動アイテムを削除する

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        

        if bird.wait_skill:
            """
            スキル選択画面
            """
            screen.fill((0, 0, 0))  # 黒画面
            font = pg.font.Font(None, 50)  # fontの大きさ
            text = font.render("Select Skill - 1:Durian 2:Soccerball", True, (255, 255, 255))  # 書く文字と白色
            screen.blit(text, ((WIDTH//4) - 200, HEIGHT//2))  # 描写位置
            pg.display.update()
            continue  # これがないと下のアップデートが実行されてしまうため必須

        bird.update(key_lst, screen)
        beams.update(xbeam)
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gravities.update()
        gravities.draw(screen)
        drns.update()
        drns.draw(screen)
        #for emy in emys:
        #    balls.update(emy)  # スキル機能のアップデート
        balls.draw(screen)  # スキル機能の描画
        items.draw(screen)  # 強化アイテムを画面に描画
        gravityitems.draw(screen)  # 重力場発動アイテムを画面に描画
        score.update(screen)
        cemys.update()
        cemys.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
