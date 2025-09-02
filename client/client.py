import pygame
from service import Service

width = 500
height = 500
win = pygame.display.set_mode((width,height))
pygame.display.set_caption("client")

clientnumber = 0


class Player():
    def __init__(self,x,y,width,height,color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = (x,y,width,height)
        self.vel = 3

    def draw(self, win):
        pygame.draw.rect(win,self.color,self.rect)

    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self.vel
        if keys[pygame.K_RIGHT]:
            self.x += self.vel
        if keys[pygame.K_UP]:
            self.y -= self.vel
        if keys[pygame.K_DOWN]:
            self.y += self.vel
            
        self.update()

    def update(self):
        self.rect = (self.x, self.y,self.width,self.height)


def read_pos(str):
    str = str.split(",")
    return int(str[0]), int(str[1])

def write_pos(tup):
    return str(tup[0]) + "," + str(tup[1])


def redrawWindow(win,p1,p2):
    
    win.fill((255,255,255))
    p1.draw(win)
    p2.draw(win)
    pygame.display.update()




def main():

    s = Service()
    startPos = read_pos(s.getPos())

    p1 = Player(startPos[0],startPos[1],80,80,(20,200,100))
    p2 = Player(0,0,80,80,(200,20,40))
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(60)

        p2Pos = read_pos(s.send(write_pos((p1.x,p1.y))))
        p2.x = p2Pos[0]
        p2.y = p2Pos[1]
        p2.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
        p1.move()
        redrawWindow(win,p1,p2)
        
main()