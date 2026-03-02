import requests
from enum import IntEnum
import time
import json
from enum import Enum


def modular_exponentiation(base, exponential, mod):
    base = base % mod
    res = 1
    while exponential:
        if exponential & 1 == 1: #判断最后一位
            res = (res * base) % mod #为1则乘幂
        base = (base * base) % mod #累乘记录幂
        exponential >>= 1  #右移一位
    return res

#10->16
def conv(dec_number):
    hex_str = hex(dec_number)[2:]
    return hex_str

#使用枚举定义目前器具状态
class map_entry_type(IntEnum):#回合
    map_empty = 0,
    map_player_one = 1,
    map_player_two = 2,


class map():  # 棋盘
    def __init__(self, width, height): #  初始化函数   棋盘的属性有   width  宽  height  高
        self.width = width
        self.height = height
        self.map = [[0 for x in range(self.width)] for y in range(self.height)]#初始化
        self.steps = []#棋步  是列表存储

    def xiugai(self, x, y, val):#更新状态
        self.map[x][y] = val

    def getmap(self):#返回棋盘状态
        return self.map

ai_search_depth = 5#博弈树的深度
ai_limited_move_num = 20 #保留前20种进行分析


class chess_type(IntEnum):#棋形（枚举）
    none = 0,#
    sleep_two = 1,#
    live_two = 2,
    sleep_three = 3
    live_three = 4,
    chong_four = 5,
    live_four = 6,
    live_five = 7,


chess_type_num = 8#八种棋形
#使用枚举
FIVE = chess_type.live_five.value
FOUR, THREE, TWO = chess_type.live_four.value, chess_type.live_three.value, chess_type.live_two.value
SFOUR, STHREE, STWO = chess_type.chong_four.value, chess_type.sleep_three.value, chess_type.sleep_two.value

score_max = 0x7fffffff#max层
score_min = -1 * score_max#min层
#各种棋形的权值
score_five, score_four, score_sfour = 100000, 10000, 1000
score_three, score_sthree, score_two, score_stwo = 100, 10, 8, 2



class ChessAI():
    def __init__(self, chess_len):
        self.len = chess_len
        self.record = [[[0, 0, 0, 0] for x in range(chess_len)] for y in range(chess_len)]
        #初始化一个三维列表 chesslen*chesslenn  且每个位置又有四个元素,为了标记已经记录过的点，防止重复分析
        self.count = [[0 for x in range(chess_type_num)] for i in range(2)]
        #初始化一个  8（棋形数）*2 的列表，用于跟踪两种玩家的棋形状态

    def reset(self):#重置棋形状态
        for y in range(self.len):
            for x in range(self.len):
                for i in range(4):
                    self.record[y][x][i] = 0

        for i in range(len(self.count)):
            for j in range(len(self.count[0])):
                self.count[i][j] = 0

    def isWin(self, board, turn):#赢了
        return self.evaluate(board, turn, True)

    # 模拟在候选点落子，评估该点对双方的价值 攻防评分
    def evaluatePointScore(self, board, x, y, mine, opponent):
        dir_offset = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 四个方向
        for i in range(len(self.count)):
            for j in range(len(self.count[0])):
                self.count[i][j] = 0
        # 16*8

        board[y][x] = mine
        self.evaluatePoint(board, x, y, mine, opponent, self.count[mine - 1])
        mine_count = self.count[mine - 1]
        board[y][x] = opponent
        self.evaluatePoint(board, x, y, opponent, mine, self.count[opponent - 1])
        opponent_count = self.count[opponent - 1]
        board[y][x] = 0

        mscore = self.getPointScore(mine_count)#调用函数分析棋型
        oscore = self.getPointScore(opponent_count)

        return (mscore, oscore)

    # 在radius范围内是否下了棋
    def hasNeighbor(self, board, x, y, radius):
        start_x, end_x = (x - radius), (x + radius)
        start_y, end_y = (y - radius), (y + radius)

        for i in range(start_y, end_y + 1):
            for j in range(start_x, end_x + 1):
                if i >= 0 and i < self.len and j >= 0 and j < self.len:
                    if board[i][j] != 0:
                        return True
        return False

    def has_double_threat(self, board, turn):
        """
        检查是否存在两个及以上活三（对手即将双杀）
        """
        self.reset()
        opponent = 2 if turn == 1 else 1
        for y in range(self.len):
            for x in range(self.len):
                if board[y][x] == opponent:
                    self.evaluatePoint(board, x, y, opponent, turn, None)

        count = self.count[opponent - 1]
        return count[THREE] >= 2 or (count[THREE] >= 1 and count[SFOUR] >= 1)

    # 获取棋子周围所有位置分数并在排序后返回最大值
    def genmove(self, board, turn):
        fives = []
        mfours, ofours = [], []
        msfours, osfours = [], []
        othrees = []

        if turn == map_entry_type.map_player_one:
            mine = 1
            opponent = 2
        else:
            mine = 2
            opponent = 1

        moves = []
        radius = 2

        for y in range(self.len):
            for x in range(self.len):
                if board[y][x] == 0 and self.hasNeighbor(board, x, y, radius):
                    mscore, oscore = self.evaluatePointScore(board, x, y, mine, opponent)
                    point = (max(mscore, oscore), x, y)
                    #位置为空且周围有棋子则评估分数记录位置

                    if mscore >= score_five or oscore >= score_five:
                        fives.append(point)
                    elif mscore >= score_four:
                        mfours.append(point)
                    elif oscore >= score_four:
                        ofours.append(point)
                    elif mscore >= score_sfour:
                        msfours.append(point)
                    elif oscore >= score_sfour:
                        osfours.append(point)
                    elif oscore >= score_three:
                        othrees.append(point)

                    moves.append(point) #所有候选位置

        # --- 优先级策略开始 ---
        if fives:
            return fives  # 直接胜利或防止被五连

        if ofours:  # 对手活四，必须第一时间拦
            return ofours

        if osfours:  # 对手冲四
            return osfours

        # 检查对手是否存在两个活三（双三必杀）
        if len(othrees) >= 2:
            return othrees

        if mfours:
            return mfours  # 自己活四，抢胜

        if ofours:
            if not msfours:
                return ofours  # 对手活四需强拦截
            else:
                return ofours + msfours

        if msfours:
            return msfours  # 自己冲四也可造胜局

        if osfours:
            if not mfours and not msfours:
                return osfours  # 拦截对手冲四（新加）

        if othrees:
            if not mfours and not msfours:
                return othrees  # 新增：提前拦截对手活三成势


        # 排序剪枝
        moves.sort(reverse=True)
        if self.maxdepth > 2 and len(moves) > ai_limited_move_num:
            moves = moves[:ai_limited_move_num]

        return moves

    def __search(self, board, turn, depth, alpha=score_min, beta=score_max):#ab剪枝 递归搜索5论找最佳骡子点

        score = self.evaluate(board, turn,False)
        if depth <= 0 or abs(score) >= score_five:#深度优先搜索结束标志，到叶节点
            return score
        moves = self.genmove(board, turn)#找点且给其打分之后排序
        bestmove = None#存最佳位置
        #如果没有找到点
        if len(moves) == 0:
            return score
        for _, x, y in moves:
            board[y][x] = turn
            if turn == map_entry_type.map_player_one:#对方
                op_turn = map_entry_type.map_player_two
            else:
                op_turn = map_entry_type.map_player_one

            score = - self.__search(board, op_turn, depth - 1, -beta, -alpha)#博弈树 max层加分对于min层玩家来说，就是减分
            board[y][x] = 0#递归结束时给其恢复原貌
            # alpha/beta 剪枝
            if score > alpha:
                alpha = score
                bestmove = (x, y)
                if alpha >= beta:
                    break
        if depth == self.maxdepth and bestmove:#如果回溯到了第一层
            self.bestmove = bestmove

        return alpha

    # 外部接口
    def search(self, board, turn, depth):
        self.maxdepth = depth
        self.bestmove = None
        score =self.__search(board, turn, depth)
        x = y = 0
        if self.bestmove is not None:
            x, y = self.bestmove
        return score, x, y

    def findBestChess(self, board, turn):
        time1 = time.time()
        score, x, y = self.search(board, turn, ai_search_depth)#5层
        time2 = time.time()
        return (x, y)

    def getPointScore(self, count):#单个位置棋型评分
        score = 0
        if count[FIVE] > 0:
            return score_five

        if count[FOUR] > 0:
            return score_four

        if count[SFOUR] > 1:
            score += count[SFOUR] * score_sfour
        elif count[SFOUR] > 0 and count[THREE] > 0:
            score += count[SFOUR] * score_sfour
        elif count[SFOUR] > 0:
            score += score_three

        if count[THREE] > 1:
            score += 5 * score_three
        elif count[THREE] > 0:
            score += score_three

        if count[STHREE] > 0:
            score += count[STHREE] * score_sthree
        if count[TWO] > 0:
            score += count[TWO] * score_two
        if count[STWO] > 0:
            score += count[STWO] * score_stwo

        return score

    # 算全局分数
    def getScore(self, mine_count, opponent_count):
        mscore, oscore = 0, 0
        if mine_count[FIVE] > 0:
            return (score_five, 0)
        if opponent_count[FIVE] > 0:
            return (0, score_five)

        if mine_count[SFOUR] >= 2:
            mine_count[FOUR] += 1
        if opponent_count[SFOUR] >= 2:
            opponent_count[FOUR] += 1

        if mine_count[FOUR] > 0:
            return (9050, 0)
        if mine_count[SFOUR] > 0:
            return (9040, 0)

        if opponent_count[FOUR] > 0:
            return (0, 9030)
        if opponent_count[SFOUR] > 0 and opponent_count[THREE] > 0:
            return (0, 9020)

        if mine_count[THREE] > 0 and opponent_count[SFOUR] == 0:
            return (9010, 0)

        if (opponent_count[THREE] > 1 and mine_count[THREE] == 0 and mine_count[STHREE] == 0):
            return (0, 9000)

        if opponent_count[SFOUR] > 0:
            oscore += 400

        if mine_count[THREE] > 1:
            mscore += 500
        elif mine_count[THREE] > 0:
            mscore += 100

        if opponent_count[THREE] > 1:
            oscore += 2000
        elif opponent_count[THREE] > 0:
            oscore += 400

        if mine_count[STHREE] > 0:
            mscore += mine_count[STHREE] * 10
        if opponent_count[STHREE] > 0:
            oscore += opponent_count[STHREE] * 10

        if mine_count[TWO] > 0:
            mscore += mine_count[TWO] * 6
        if opponent_count[TWO] > 0:
            oscore += opponent_count[TWO] * 6

        if mine_count[STWO] > 0:
            mscore += mine_count[STWO] * 2
        if opponent_count[STWO] > 0:
            oscore += opponent_count[STWO] * 2

        return (mscore, oscore)

    def evaluate(self, board, turn, checkWin=False):#评估局势
        self.reset()#重置
        if turn == map_entry_type.map_player_one:
            mine = 1
            opponent = 2
        else:
            mine = 2
            opponent = 1

        for y in range(self.len):
            for x in range(self.len):
                if board[y][x] == mine:
                    self.evaluatePoint(board, x, y, mine, opponent,None)
                elif board[y][x] == opponent:
                    self.evaluatePoint(board, x, y, opponent, mine,None)

        mine_count = self.count[mine - 1]
        opponent_count = self.count[opponent - 1]
        if checkWin:
            return mine_count[FIVE] > 0
        else:
            mscore, oscore = self.getScore(mine_count, opponent_count)
            return (mscore - oscore)

    def evaluatePoint(self, board, x, y, mine, opponent, count=None):#单个棋子在四个方向的棋型
        dir_offset = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 看棋子的四周
        ignore_record = True
        if count is None:
            count = self.count[mine - 1]#当前角色的有的棋型
            ignore_record = False
        for i in range(4):
            if self.record[y][x][i] == 0 or ignore_record:
                self.analysisLine(board, x, y, i, dir_offset[i], mine, opponent, count)#分别在四个方向上分析行
                #self, board, x, y, dir_index, dir, mine, opponent, count
    # line is fixed len 9: XXXXMXXXX

    def getLine(self, board, x, y, dir_offset, mine, opponent):#辅助 分析指定方向九个位置的棋子分布
        line = [0 for i in range(9)]

        tmp_x = x + (-5 * dir_offset[0])
        tmp_y = y + (-5 * dir_offset[1])
        for i in range(9):
            tmp_x += dir_offset[0]
            tmp_y += dir_offset[1]
            if (tmp_x < 0 or tmp_x >= self.len or
                    tmp_y < 0 or tmp_y >= self.len):
                line[i] = opponent  #出界了就认为是对方的棋子
            else:
                line[i] = board[tmp_y][tmp_x]

        return line

    def analysisLine(self, board, x, y, dir_index, dir, mine, opponent, count):#分析指定方向的棋型
        # record line range[left, right] as analysized
        def setRecord(self, x, y, left, right, dir_index, dir_offset):#标记已经下好的点
            tmp_x = x + (-5 + left) * dir_offset[0]
            tmp_y = y + (-5 + left) * dir_offset[1]
            for i in range(left, right + 1):
                tmp_x += dir_offset[0]
                tmp_y += dir_offset[1]
                self.record[tmp_y][tmp_x][dir_index] = 1

        empty = map_entry_type.map_empty.value#棋盘为空的时候的模式

        left_idx, right_idx = 4, 4#找到最中间的那个 和我们最开始的点偏一个

        line = self.getLine(board, x, y, dir, mine, opponent)

        while right_idx < 8:#右边到第几个不是自己，下标停在最后一个自己
            if line[right_idx + 1] != mine:
                break
            right_idx += 1
        while left_idx > 0:#左边到第几个不是自己
            if line[left_idx - 1] != mine:
                break
            left_idx -= 1

        left_range, right_range = left_idx, right_idx#统计下标

        while right_range < 8:#判断右边第几个是敌人，停在敌人的上一个
            if line[right_range + 1] == opponent:
                break
            right_range += 1
        while left_range > 0:#判断左边第几个是敌人
            if line[left_range - 1] == opponent:
                break
            left_range -= 1

        chess_range = right_range - left_range + 1#算中间有多少自己能下的位置

        if chess_range < 5:#判断
            setRecord(self, x, y, left_range, right_range, dir_index, dir)#自己的棋子加上空位都不够5个，不归为任何棋型，记录
            return chess_type.none

        setRecord(self, x, y, left_idx, right_idx, dir_index, dir)#记录

        m_range = right_idx - left_idx + 1

        # M:mine chess, P:opponent chess or out of range, X: empty
        if m_range >= 5:
            count[FIVE] += 1

        # Live Four : XMMMMX 活四
        # Chong Four : XMMMMP, PMMMMX
        if m_range == 4:
            left_empty = right_empty = False
            if line[left_idx - 1] == empty:
                left_empty = True
            if line[right_idx + 1] == empty:
                right_empty = True
            if left_empty and right_empty:
                count[FOUR] += 1#活四
            elif left_empty or right_empty:
                count[SFOUR] += 1#眠4

                # 新增：跳冲四检测 XMMM X M 或 M X MMMX
            if left_empty and right_empty:
                    # 左侧跳冲四
                    if (left_idx > 0 and line[left_idx - 1] == empty and
                            left_idx > 4 and line[left_idx - 5] == mine):
                        count[SFOUR] += 1
                    # 右侧跳冲四
                    if (right_idx < 8 and line[right_idx + 1] == empty and
                            right_idx < 4 and line[right_idx + 5] == mine):
                        count[SFOUR] += 1

        # Chong Four : MXMMM, MMMXM, the two types can both exist
        # Live Three : XMMMXX, XXMMMX
        # Sleep Three : PMMMX, XMMMP, PXMMMXP
        if m_range == 3:
            left_empty = right_empty = False
            left_four = right_four = False
            if line[left_idx - 1] == empty:
                if line[left_idx - 2] == mine:  # MXMMM
                    setRecord(self, x, y, left_idx - 2, left_idx - 1, dir_index, dir)
                    count[SFOUR] += 1
                    left_four = True
                left_empty = True

            if line[right_idx + 1] == empty:
                if line[right_idx + 2] == mine:  # MMMXM
                    setRecord(self, x, y, right_idx + 1, right_idx + 2, dir_index, dir)
                    count[SFOUR] += 1
                    right_four = True
                right_empty = True

            if left_four or right_four:
                pass
            elif left_empty and right_empty:
                if chess_range > 5:  # XMMMXX, XXMMMX
                    count[THREE] += 1
                else:  # PXMMMXP
                    count[STHREE] += 1
            elif left_empty or right_empty:  # PMMMX, XMMMP
                count[STHREE] += 1
            if left_empty and right_empty:
                # 情况1: XM MX X (中间空一格)
                if (left_idx > 1 and line[left_idx - 2] == mine and
                        line[left_idx - 1] == empty):
                    count[THREE] += 1
                # 情况2: X MM X X (右侧空一格)
                if (right_idx < 7 and line[right_idx + 2] == mine and
                        line[right_idx + 1] == empty):
                    count[THREE] += 1


        # Chong Four: MMXMM, only check right direction
        # Live Three: XMXMMX, XMMXMX the two types can both exist
        # Sleep Three: PMXMMX, XMXMMP, PMMXMX, XMMXMP
        # Live Two: XMMX
        # Sleep Two: PMMX, XMMP
        if m_range == 2:
            left_empty = right_empty = False
            left_three = right_three = False
            if line[left_idx - 1] == empty:
                if line[left_idx - 2] == mine:
                    setRecord(self, x, y, left_idx - 2, left_idx - 1, dir_index, dir)
                    if line[left_idx - 3] == empty:
                        if line[right_idx + 1] == empty:  # XMXMMX
                            count[THREE] += 1
                        else:  # XMXMMP
                            count[STHREE] += 1
                        left_three = True
                    elif line[left_idx - 3] == opponent:  # PMXMMX
                        if line[right_idx + 1] == empty:
                            count[STHREE] += 1
                            left_three = True

                left_empty = True

            if line[right_idx + 1] == empty:
                if line[right_idx + 2] == mine:
                    if line[right_idx + 3] == mine:  # MMXMM
                        setRecord(self, x, y, right_idx + 1, right_idx + 2, dir_index, dir)
                        count[SFOUR] += 1
                        right_three = True
                    elif line[right_idx + 3] == empty:
                        # setRecord(self, x, y, right_idx+1, right_idx+2, dir_index, dir)
                        if left_empty:  # XMMXMX
                            count[THREE] += 1
                        else:  # PMMXMX
                            count[STHREE] += 1
                        right_three = True
                    elif left_empty:  # XMMXMP
                        count[STHREE] += 1
                        right_three = True

                right_empty = True

            if left_three or right_three:
                pass
            elif left_empty and right_empty:  # XMMX
                count[TWO] += 1
            elif left_empty or right_empty:  # PMMX, XMMP
                count[STWO] += 1

            if left_empty or right_empty:
                    # 情况1: PM MX X 或 XM MP X
                    if (left_idx > 1 and line[left_idx - 2] == mine and
                            line[left_idx - 1] == empty):
                        count[STHREE] += 1
                    if (right_idx < 7 and line[right_idx + 2] == mine and
                            line[right_idx + 1] == empty):
                        count[STHREE] += 1

        # Live Two: XMXMX, XMXXMX only check right direction
        # Sleep Two: PMXMX, XMXMP
        if m_range == 1:
            left_empty = right_empty = False
            if line[left_idx - 1] == empty:
                if line[left_idx - 2] == mine:
                    if line[left_idx - 3] == empty:
                        if line[right_idx + 1] == opponent:  # XMXMP
                            count[STWO] += 1
                left_empty = True

            if line[right_idx + 1] == empty:
                if line[right_idx + 2] == mine:
                    if line[right_idx + 3] == empty:
                        if left_empty:  # XMXMX
                            # setRecord(self, x, y, left_idx, right_idx+2, dir_index, dir)
                            count[TWO] += 1
                        else:  # PMXMX
                            count[STWO] += 1
                elif line[right_idx + 2] == empty:
                    if line[right_idx + 3] == mine and line[right_idx + 4] == empty:  # XMXXMX
                        count[TWO] += 1

        return chess_type.none

def play_game(coord):#落子坐标写如crood字段
    print("我落子:" + coord)
    game_id_encoded = str(game_id)
    coord_encoded = coord
    param={'user': user, 'password': password,'coord': coord_encoded,'data_type':'json'}
    req = requests.get(f'http://183.175.12.27:8004/play_game/'+str(game_id),params=param)
def join_game(user,password):
    req = requests.get(f'http://183.175.12.27:8004/join_game?user={user}&password={password}&data_type=json')
    g_i = req.json()['game_id']
    return g_i
def do_check_game():  # 检查游戏状态
    r = requests.get(f'http://183.175.12.27:8004/check_game/' + str(game_id))
    return r
def getmap(request):
    global map
    if request['ready']:
        if request['current_turn'] == user and request['last_step'] != '':  # 上一步是对方下的
            coord = request['last_step']
            x = int(ord(coord[0]) - ord('a'))
            y = int(ord(coord[1]) - ord('a'))
            map.xiugai(x, y, 2)
        # 当上一步是我下的时候，这里不做处理，在获取点时处理



ChessAI = ChessAI(15)  # 创建示例
map = map(15, 15)  # 创建实例



def play():
    if check_url.json()['current_turn'] != user:
        print("等待对方落子")
        return
    else:
        if check_url.json()['board'] == '':#第一步  放中间
            map.xiugai(7, 7, 1)
            play_game("hh")
            #chessboard[7][7] = check_url.json()['current_stone']
        else:

            getmap(request)
            y, x = ChessAI.findBestChess(map.getmap(), 1)
            ansstr = ''
            ansstr = chr(x + ord('a')) + chr(y + ord('a'))
            play_game(ansstr)
            map.xiugai(x, y, 1)
           # p = ord(next_step[1]) - 97
            #q = ord(next_step[0]) - 97
            #chessboard[p][q]=check_url.json()['current_stone']
            #if(check_url.json()['current_stone'] == "x"):
             #   chessboard[p][q]='x'
            #else:
             #   chessboard[p][q]='o'


#密码加密
exp = 65537
m = 135261828916791946705313569652794581721330948863485438876915508683244111694485850733278569559191167660149469895899348939039437830613284874764820878002628686548956779897196112828969255650312573935871059275664474562666268163936821302832645284397530568872432109324825205567091066297960733513602409443790146687029
str1="BAIAN123"
num = list(str1)
str2 = []
for i in reversed(num):
    str2.append(i)
asn = 0
a = 0
for i in str2:
    asn = asn + ord(i) * 256 ** a
    a = a + 1
self = asn
#登录，加入游戏
password=conv(modular_exponentiation(self,exp,m))
user="0231123923"
game_id=join_game(user,password)
'''chessboard = ["...............", "...............", "...............", "...............", "...............",
                  "...............", "...............", "...............", "...............", "...............",
                  "...............", "...............", "...............", "...............", "..............."]'''
while True:

    # 检查状态的网址
    check_url = requests.get(f'http://183.175.12.27:8004/check_game/' + str(game_id))
    request = do_check_game()
    request = request.json()
    winner = check_url.json()['winner']
    #print(check_url.status_code)  # 打印状态码
    if winner == 'None':
        if check_url.json()['ready'] == "False":
            continue
        else:
            print(check_url.json()['creator']+":"+check_url.json()['creator_stone'])
            print(check_url.json()['opponent']+":"+check_url.json()['opponent_stone'])
            play()
    else:
        print("胜利者:" + check_url.json()['winner'])
        break
    time.sleep(15)



