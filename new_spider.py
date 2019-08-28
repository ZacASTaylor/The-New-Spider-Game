# Zachary Stroud-Taylor
# Carleton University

# Optimized all three searches
# Faster Ant
# Removed parent dict from A* searches

from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox

from math import hypot
from time import process_time
from random import randint, choice
from heapq import heappush, heappop


# Board object used by entities to determine their coordinates and where to draw
class Board(object):
    def __init__(self, window, gridSqrPxs, dim, pad):
        self.window = window
        self.gridSqrPxs = gridSqrPxs
        self.dim = dim
        self.pad = pad


# ~Abstract entity class 
class Entity(object):
    def __init__(self, board):
        self.gridCoords = None
        self.drawCoords = None
        self.sprite = None
        self.board = board
    
    # Private methods for all concrete entites to use
    
    def _randSquare(self):
        x = randint(1, self.board.dim)
        y = randint(1, self.board.dim)
        return (x, y)
    
    def _computeDrawCoords(self):
        x = self.gridCoords[0]
        y = self.gridCoords[1]
        return [ (x-1) * self.board.gridSqrPxs + self.board.pad, 
                 (y-1) * self.board.gridSqrPxs + self.board.pad, 
                 x     * self.board.gridSqrPxs + self.board.pad, 
                 y     * self.board.gridSqrPxs + self.board.pad ]      
        
    def _left(self, event=None):
        self.drawCoords[0] -= self.board.gridSqrPxs
        self.drawCoords[2] -= self.board.gridSqrPxs
        self.gridCoords = (self.gridCoords[0]-1, self.gridCoords[1])
 
    def _right(self, event=None):
        self.drawCoords[0] += self.board.gridSqrPxs
        self.drawCoords[2] += self.board.gridSqrPxs
        self.gridCoords = (self.gridCoords[0]+1, self.gridCoords[1])
    
    def _up(self, event=None):
        self.drawCoords[1] -= self.board.gridSqrPxs
        self.drawCoords[3] -= self.board.gridSqrPxs
        self.gridCoords = (self.gridCoords[0], self.gridCoords[1]-1)
    
    def _down(self, event=None):
        self.drawCoords[1] += self.board.gridSqrPxs
        self.drawCoords[3] += self.board.gridSqrPxs
        self.gridCoords = (self.gridCoords[0], self.gridCoords[1]+1)
        
    def move(self, newGridCoords):
        while(True):
            if newGridCoords == self.gridCoords:
                break
            if newGridCoords[0] > self.gridCoords[0]:
                self._right()
            if newGridCoords[0] < self.gridCoords[0]:
                self._left()
            if newGridCoords[1] > self.gridCoords[1]:
                self._down()
            if newGridCoords[1] < self.gridCoords[1]:
                self._up()
                
    def draw(self):
        self.board.window.delete(self.sprite)
        self.sprite = self.board.window.create_rectangle(self.drawCoords, fill=self.color)
        
    def delete(self):
        self.board.window.delete(self.sprite)  

# Human controlled entity, used for testing before, not used anymore
class HCEntity(Entity):   
    def __init__(self, board, color="blue"):
        super(HCEntity, self).__init__(board)
        coordList = self.randSquare()
        self.gridCoords = self._randSquare()
        self.drawCoords = self._computeDrawCoords()
        self.color = color
        self.sprite = self.board.window.create_rectangle(self.drawCoords, fill=self.color)


# Random moving target entity for spider 
class Ant(Entity):
    def __init__(self, board, speed, color="black"):
        super(Ant, self).__init__(board)
        self.color = color
        self.speed = speed
        self.gridCoords = self._randSquare()
        self.direction = self._directionSetter()
        self.drawCoords = self._computeDrawCoords()
        self.sprite = self.board.window.create_rectangle(self.drawCoords, fill=self.color)

    def _directionSetter(self):
        possibleDirs = [ 
                         ( 0, -1), # N
                         ( 1, -1), # NE
                         ( 1,  0), # E
                         ( 1,  1), # SE
                         ( 0,  1), # S
                         (-1,  1), # SW
                         (-1,  0), # W
                         (-1, -1)  # NW
                       ]
        
        direction = None # Don't let the ant immediately walk off the board
        while (True):
            direction = choice(possibleDirs)
            x = self.gridCoords[0] + direction[0] * ((1/4) * self.board.dim)
            y = self.gridCoords[1] + direction[1] * ((1/4) * self.board.dim)
            
            if x > 0 and x < self.board.dim and y > 0 and y < self.board.dim:
                break # Accept the direction if the ant won't walk off the 
                      # board in an amount of steps less than a quarter of the
                      # size of the board dimensions
                
        direction = (direction[0]*self.speed, direction[1]*self.speed)
        
        return direction
    
    def _computeDrawCoords(self):
        coords = super(Ant, self)._computeDrawCoords()
        coords[0] += 3
        coords[1] += 6
        coords[2] -= 3
        coords[3] -= 6
        return coords
    
    # Overridden from abstract entity 
    def move(self):       
        newX = self.gridCoords[0] + self.direction[0]
        newY = self.gridCoords[1] + self.direction[1]
        super(Ant, self).move((newX, newY))
          
          
# Search path following seeking entity  
class Spider(Entity):
    def __init__(self, board, color="blue"):
        super(Spider, self).__init__(board)
        self.color = color
        self.gridCoords = self._randSquare()
        self.drawCoords = self._computeDrawCoords()
        self.sprite = self.board.window.create_rectangle(self.drawCoords, fill=self.color)
                     
# Class to store and manipulate spider data 
class SpiderNode(object):
    def __init__(self, spiderCoords, antCoords, parent, depth, hValue=None):
        self.spiderCoords = spiderCoords
        self.antCoords = antCoords
        self.children = [] # possible spider locations
        self.parent = parent
        self.depth = depth
        self.hValue = hValue
        
        x = self.spiderCoords[0]
        y = self.spiderCoords[1]
        
        # Counter clockwise from 12 o'clock all posible spider moves
        self.children.append((x+1, y-2))
        self.children.append((x+2, y-1))
        self.children.append((x+1, y))
        
        self.children.append((x+1, y+1))
        self.children.append((x, y+1))
        self.children.append((x-1, y+1))
        
        self.children.append((x-1, y))
        self.children.append((x-2, y-1))
        self.children.append((x-1, y-2))

    def __key(self):
        return (self.spiderCoords + self.antCoords)

    def __hash__(self):
        return hash(self.__key())
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.__key() == other.__key())
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)   
    
    def __lt__(self, other):
        return (self.depth + self.hValue) < (other.depth + other.hValue)

    def __repr__(self):
        return str(self.spiderCoords)

    def __str__(self):
        return str(self.spiderCoords)
            
            
# ~Abstract search class               
class Search(object):
    def __init__(self, sType, spider, ant, boardDim):
        self.sType = sType
        self.spiderCoords = spider.gridCoords    
        self.antCoords = ant.gridCoords
        self.antStartCoords = self.antCoords                
        self.antDir = ant.direction
        self.boardDim = boardDim
        self.path = None       
        self.curr = None
        self.toVisit = []
        
    def genPath(self):
        self.path = [self.curr.spiderCoords]
        while(self.curr.parent != None): # Path back to start
            self.curr = self.curr.parent
            self.path.insert(0, self.curr.spiderCoords)
        self.path = self.path[1:] # Slice to remove coords spider is already on        
     
    def bothEntitiesOnBoard(self, childPosition):
        if (childPosition[0] > 0 and childPosition[0] <= self.boardDim):# Spider x bound still on board
            if (childPosition[1] > 0 and childPosition[1] <= self.boardDim):# Spider y bound still on board
                if((self.antCoords[0] > 0) and (self.antCoords[0] <= self.boardDim)): # Ant x bound still on board
                    return ((self.antCoords[1] > 0) and (self.antCoords[1] <= self.boardDim)) # Ant y bound still on board


# BFS and DFS (toggled with sType) class concrete search class
class BlindSearch(Search):    
    
    def __init__(self, sType, spider, ant, boardDim):
        super(BlindSearch, self).__init__(sType, spider, ant, boardDim)

        self.visited = {}        
        self.toVisit.append(SpiderNode(self.spiderCoords, self.antCoords, None, 0)) # No parent and depth is 0
        self.visited[self.toVisit[0]] = True        
    
        self.loop()
        
    # Search loop    
    def loop(self):
        
        while len(self.toVisit) != 0:
            
            if self.sType == "DFS":
                self.curr = self.toVisit[len(self.toVisit)-1]
            else: 
                self.curr = self.toVisit[0]                 
            
            self.toVisit.remove(self.curr)
                        
            self.antCoords = (self.antStartCoords[0] + (self.curr.depth * self.antDir[0]),
                              self.antStartCoords[1] + (self.curr.depth * self.antDir[1])) 

            if self.antCoords == self.curr.spiderCoords:
                self.genPath()
                print(self.sType + " There is a path!")                
                break        
        
            for c in self.curr.children:
                if self.bothEntitiesOnBoard(c):            
                    newNode = SpiderNode(c, self.antCoords, self.curr, (self.curr.depth+1)) # Create node so it can be checked against lists
                    if newNode not in self.visited:
                        self.toVisit.append(newNode)
                        self.visited[newNode] = True

        if self.path == None:                
            print(self.sType + " No path!")              
   

# A* search class concrete search class           
class AStarSearch(Search):
    
    def __init__(self, sType, spider, ant, boardDim):
        super(AStarSearch, self).__init__(sType, spider, ant, boardDim)
        
        # Assign heuristic type
        if self.sType == "A*1":
            self.hCalc = self.aS1HCalc        
        elif self.sType == "A*2":
            self.hCalc = self.aS2HCalc        
        elif self.sType == "A*3":
            self.hCalc = self.aS3HCalc
        
        firstHVal = self.hCalc(self.spiderCoords, self.antCoords)
        first = SpiderNode(self.spiderCoords, self.antCoords, None, 0, firstHVal)
        heappush(self.toVisit, first)
        
        self.depth = {first: 0}        
    
        self.loop()
    
    # Search loop    
    def loop(self):
        
        while len(self.toVisit) != 0:        
            
            self.curr = heappop(self.toVisit)
            
            self.antCoords = (self.antStartCoords[0] + (self.curr.depth * self.antDir[0]),
                              self.antStartCoords[1] + (self.curr.depth * self.antDir[1])) 
    
            if self.antCoords == self.curr.spiderCoords:
                self.genPath()
                print(self.sType + " There is a path!")                
                break
        
            for c in self.curr.children:
                
                if self.bothEntitiesOnBoard(c):
                    newNodeHVal = self.hCalc(c, self.antCoords)
                    newNode = SpiderNode(c, self.antCoords, self.curr, (self.curr.depth+1), newNodeHVal) # Create node so it can be checked against lists                    
                    
                    if newNode not in self.depth or newNode.depth < self.depth[newNode]: 
                        self.depth[newNode] = newNode.depth
                        heappush(self.toVisit, newNode)
                
        if self.path == None:                
            print(self.sType + " No path!")  
            
        
    def aS1HCalc(self, spiderCoords, antCoords):
        x1, y1 = spiderCoords
        x2, y2 = antCoords
        return (hypot(x2-x1, y2-y1) / 2.5)
    
    def aS2HCalc(self, spiderCoords, antCoords):
        x1, y1 = spiderCoords
        x2, y2 = antCoords
        return  (1/3) * (abs(x2-x1) + abs(y2-y1)) # Cut in half because some steps can move two values (so as to always underestimate)
        
    
    def aS3HCalc(self, spiderCoords, antCoords):
        hOne = self.aS1HCalc(spiderCoords, antCoords)
        hTwo = self.aS2HCalc(spiderCoords, antCoords)
        return (0.5 * (hOne + hTwo))
    
    
# Game controller class
class SpiderGame():  

    def startMenu(self):
        
        # Add warnings for too few or too many ants and spiders
        #                                 Must assign different colors or numbers if multiple spiders or ants 
        Label(self.master, text="Number of Spiders: ", font=("time",16)).grid(row=0, padx=(10,0), pady=(4,0), sticky=E)
        self.spiderEntry = Entry(self.master, width=3, justify='center', font=("time",16))
        self.spiderEntry.insert(END, 1)
        self.spiderEntry.grid(row=0, column=1, padx=(0,10), pady=(4,0))
        
        Label(self.master, text="Number of Ants: ", font=("time",16)).grid(row=1, sticky=E, pady=(4,0))
        self.antEntry = Entry(self.master, width=3, justify='center', font=("time",16))
        self.antEntry.insert(END, 1)
        self.antEntry.grid(row=1, column=1, padx=(0,10), pady=(4,0))
        
        Label(self.master, text="Dimensions: ", font=("time",16)).grid(row=2, sticky=E, pady=(4,0))
        self.dimEntry = Entry(self.master, width=3, justify='center', font=("time",16))
        self.dimEntry.insert(END, 20)
        self.dimEntry.grid(row=2, column=1, padx=(0,10), pady=(4,0))
        
        Label(self.master, text="Ant Speed: ", font=("time",16)).grid(row=3, sticky=E, pady=(4,0))
        antSpeedChoices = (1, 2, 3)
        self.antSpeedEntry = IntVar(self.master) # Special Tkinter variable needed for OptionMenu
        self.antSpeedEntry.set(1) # set the default option
        antSpeedDropMenu = OptionMenu(self.master, self.antSpeedEntry, *antSpeedChoices)
        antSpeedDropMenu.config(font=("time",16))
        antSpeedDropMenu.grid(row=3, column=1, padx=(0,10), pady=(4,0))    
        
        Label(self.master, text="Search Type: ", font=("time",16)).grid(row=4, sticky=E, pady=(4,0))
        searchChoices = ('BF','DF','A*1','A*2','A*3')
        self.searchEntry = StringVar(self.master) # Special Tkinter variable needed for OptionMenu
        self.searchEntry.set('BF') # set the default option
        searchDropMenu = OptionMenu(self.master, self.searchEntry, *searchChoices)
        searchDropMenu.config(font=("time",16))
        searchDropMenu.grid(row=4, column=1, padx=(0,10), pady=(4,0))
        
        # Which searches to run
        #Label(self.master, text="BFS:").grid(row=4, sticky=E, pady=(4,0))
        #var1 = IntVar()
        #Checkbutton(self.master, variable=var1).grid(row=4, column=1, padx=(0,10), pady=(4,0))
        
        goButtton = Button(self.master, text="Go!", font=("time",16), 
                           command=lambda:self.initGame()).grid(row=5, column=0, columnspan=2)
        
        self.master.bind('<Return>', self.initGame)
        
        self.master.mainloop()        
    
    def initGame(self, event=None):
        
        self.master.unbind('<Return>')

        # Convert string inputs to ints
        # and get drop down menu values
        self.spiderEntry = int(self.spiderEntry.get())
        self.antEntry = int(self.antEntry.get())
        self.dimEntry = int(self.dimEntry.get())
        self.antSpeedEntry = int(self.antSpeedEntry.get())
        self.searchEntry = self.searchEntry.get()     
        
        # Get all drawn children and erase them all
        kids = self.all_children(self.master)
        for k in kids:
            k.grid_forget()
         
        self.draw()  
        self.master.after(10, self.search)

    def all_children (self, window) :
        # this function is from https://stackoverflow.com/questions/45905665/is-there-a-way-to-clear-all-widgets-from-a-tkinter-window-in-one-go-without-refe?noredirect=1&lq=1
        _list = window.winfo_children()
    
        for item in _list :
            if item.winfo_children() :
                _list.extend(item.winfo_children())   
        return _list    
    
    def draw(self):
        self.pad = 2
        self.gridSqrPxs = 15
        self.dimPx = self.dimEntry * self.gridSqrPxs + self.pad
        self.window = Canvas(self.master, width=self.dimPx, height=self.dimPx)
        self.window.pack()    
        
        for i in range(self.pad, self.dimPx+1, self.gridSqrPxs): 
            self.window.create_line(i, 0, i, self.dimPx)
            self.window.create_line(0, i, self.dimPx, i)
        
        # gridSqrPxs is the number of pixel per grid square
        # dimEntry is the side length of the sqaure grid in units of grid squares
        self.board = Board(self.window, self.gridSqrPxs, self.dimEntry, self.pad)
        
        # Can't let ants and spiders have same starting square
        # Add warnings for too few or too many ants and spiders
        #                                 Must assign different colors or numbers if multiple spiders or ants        
        self.spider = Spider(self.board, "black")
        self.ant = Ant(self.board, self.antSpeedEntry, "black")
        self.noPathLabel = None
    
    # Game controlling search
    def search(self):
        # Multiple ants and spiders?          

        # BFS
        start = process_time()
        bfs = BlindSearch("BFS", self.spider, self.ant, self.board.dim)
        print("BFS time:", process_time()-start)
        print("BFS len:", len(bfs.path if bfs.path != None else []))
        print()
        
        # DFS
        start = process_time()        
        dfs = BlindSearch("DFS", self.spider, self.ant, self.board.dim)
        print("DFS time:", process_time()-start)
        print("DFS len:", len(dfs.path if dfs.path != None else []))
        print()
     
        # A*1
        start = process_time()                
        aS1 = AStarSearch("A*1", self.spider, self.ant, self.board.dim)
        print("A*1 time:", process_time()-start)
        print("A*1 len:", len(aS1.path if aS1.path != None else []))
        print()
        
        # A*2
        start = process_time()                
        aS2 = AStarSearch("A*2", self.spider, self.ant, self.board.dim)
        print("A*2 time:", process_time()-start)
        print("A*2 len:", len(aS2.path if aS2.path != None else []))
        print()
        
        # A*3
        start = process_time()                
        aS3 = AStarSearch("A*3", self.spider, self.ant, self.board.dim)
        print("A*3 time:", process_time()-start)
        print("A*3 len:", len(aS3.path if aS3.path != None else []))
        print()        
        
        if self.searchEntry == "BF":
            path = bfs.path
            
        elif self.searchEntry == "DF":
            path = dfs.path
            
        elif self.searchEntry == "A*1":
            path = aS1.path  
            
        elif self.searchEntry == "A*2":
            path = aS2.path  
            
        elif self.searchEntry == "A*3":
            path = aS3.path
        
        if path != None:
            print("Executing " + self.searchEntry + " path...")
            print()
        else:
            self.noPathLabel = Label(self.master, text="No Viable Path", font=("time",16), fg='red')
            self.noPathLabel.pack()       
            
        self.master.after(500, lambda:self.gameloop(path))
    
    def newAnt(self):
        self.ant.delete()
        self.ant = Ant(self.board, self.antSpeedEntry,"black")
        self.ant.draw()
        self.master.after(500, self.search)           
    
    def gameloop(self, path):

        if self.ant.gridCoords == self.spider.gridCoords:
            self.antsEaten += 1
            messagebox.showinfo("Congratualtions", "Ladies and gentlemen, we got 'im!\nAnts Eaten: " + str(self.antsEaten) + "\nAnts Lost: " + str(self.antsLost))
            self.newAnt()
            if self.noPathLabel:
                self.noPathLabel.destroy()  
                
        elif (self.ant.gridCoords[0] > self.board.dim or 
        self.ant.gridCoords[0] < 1 or
        self.ant.gridCoords[1] > self.board.dim or 
        self.ant.gridCoords[1] < 1):
            self.antsLost += 1            
            messagebox.showerror("Sad... just sad.", "He got away again...\nAnts Eaten: " + str(self.antsEaten) + "\nAnts Lost: " + str(self.antsLost))         
            self.newAnt()
            if self.noPathLabel:
                self.noPathLabel.destroy()    
                
        else:
            self.ant.move()        
            self.ant.draw()
            
            if ((path == None) or (path == [])):
                self.master.after(500, lambda:self.gameloop(None))            
        
            elif len(path) == 1:
                self.spider.move(path[0])                
                self.spider.draw()                
                self.master.after(500, lambda:self.gameloop(None))
                
            else:
                self.spider.move(path[0])                
                self.spider.draw()                
                self.master.after(500, lambda:self.gameloop(path[1:]))

    def __init__(self):
        self.master = Tk()
        self.master.title("NEW SPIDER")
        self.master.iconbitmap(r'.\\resources\\spider-icon.ico')
        self.antsEaten = 0
        self.antsLost = 0        
        self.startMenu()


SpiderGame()