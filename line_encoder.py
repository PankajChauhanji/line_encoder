# Importing matplotlib library
import matplotlib.pyplot as plt


def nrz_l(inp):
    """NRZ-L Encoder
    Input:list of input bits
    Output: list of Decoded bits"""
    # inp1=list(inp)
    # inp1.insert(0,0)
    # inp1=[-1 if i==0 else 1 for i in inp1]
    # return inp1
    inp1 = list(inp)
    inp2 = []
    for i in inp1:
        if i == 0:
            inp2.append(1)
        else:
            inp2.append(-1)
    return inp2

def nrz_i(inp):
    """ NRZ-I Encoder
        Input:list of input bits
        Output: list of Decoded bits"""
    inp2=list(inp)
    get=False
    for i in range(len(inp2)):
        if inp2[i]==1 and not get:
            get=True
            continue
        if get and inp2[i]==1:
            if inp2[i-1]==0:
                inp2[i]=1
                continue
            else :
                inp2[i]=0
                continue
        if get:
            inp2[i]=inp2[i-1]
    inp2=[-1 if i==0 else 1 for i in inp2]       
    return inp2
    
def manchester(inp):
    """ Manchester Encoder
        Input:list of input bits
        Output: list of Decoded bits"""
    inp1=list(inp)
    li,init=[],False
    for i in range(len(inp1)):
        if inp1[i]==0:
            li.append(-1)
            if not init:
                li.append(-1)
                init=True
            li.append(1)
        elif inp1[i]==1 :
            li.append(1)
            li.append(-1)
    print(inp)
    print(li)
    return li        
    

def Differential_manchester(inp):
    """ Diffferential Encoder
        Input:list of input bits
        Output: list of Decoded bits"""
    inp1=list(inp)
    li,lock,pre=[],False,''
    for i in range(len(inp1)):
        if inp1[i]==0 and not lock:
            li.append(-1)
            li.append(-1)
            li.append(1)
            lock=True
            pre='S'
        elif inp1[i]==1 and not lock :
            li.append(1)
            li.append(1)
            li.append(-1)
            lock=True
            pre='Z'
        else:
            if inp1[i]==0:
                if pre=='S':
                    li.append(-1);li.append(1)
                else:
                    li.append(1);li.append(-1)
            else:
                if pre=='Z':
                    pre='S'
                    li.append(-1);li.append(1)
                else:
                    pre='Z'
                    li.append(1);li.append(-1)
                         
    return li                        

def AMI(inp):
    """ AMI Encoder
        Input:list of input bits
        Output: list of Decoded bits"""
    inp1=list(inp)
    inp1.insert(0,0)
    lock=False
    for i in range(len(inp1)):
        if inp1[i]==1 and not lock:
            lock=True
            continue
        elif lock and inp1[i]==1:
            inp1[i]=-1
            lock=False
    return inp1  

def b8zs(inp):
    inp1 = list(inp)
    rule = ['0','0','0','v','b','0','v','b']
    i = 0
    while(i!=len(inp1)):
        if i == 1:
            prev = 1
        if i == -1:
            prev = 1
        if inp1[i]==0:
            count = 0
            for j in range(i,8+i,1):
                if inp1[j] == 0:
                    count = count + 1
                else:
                    break
        if count == 8:
            inp1[i+4] == prev
            prev = -1*prev
            inp1[i+5] == prev
            inp1[i+6] == prev
            prev = -1*prev
            inp1[i+7] ==prev
            i = i+8
        else:
            i = i+1
        return inp1

                
if __name__=='__main__':
    print("Enter the following options:")
    print("1 : NRZ-I\n2 : NRZ-L\n3 : Manchester\n4 : DIFFERENTIAL MANCHESTER\n 5: AMI")
    ch = int(input())
    print("Enter the size of Encoded Data : ")
    size=int(input())
    li=[0]
    print('Enter the binary bits sequnce of length ',size,' bits : \n')
    for i in range(size):
        li.append(int(input()))
    # li.append(0)

    plt.subplot(2,1,1)
    plt.tight_layout(pad=4)
    plt.ylabel("Bits")
    plt.title("Original Data")
    plt.plot(li,color='green',drawstyle='steps-pre')

    if (ch==1):
        plt.subplot(2,1,2)
        plt.title("Encoded Data Using NRZ-I")
        plt.ylabel("Bits")
        plt.plot(nrz_i(li),color='green',drawstyle='steps-pre')
    elif (ch==2):
        plt.subplot(2,1,2)
        plt.title("Encoded Data Using NRZ-L")
        plt.ylabel("Bits")
        plt.plot(nrz_l(li),color='green',drawstyle='steps-pre')
    elif (ch==3):
        plt.subplot(2,1,2)
        plt.title("Encoded Data Using Differential Manchester")
        plt.ylabel("Bits")
        plt.plot(manchester(li),color='green',drawstyle='steps-pre')
    elif (ch==4):
        plt.subplot(2,1,2)
        plt.title("Encoded Data Using Manchester")
        plt.ylabel("Bits")
        plt.plot(Diffferential_manchester(li),color='green',drawstyle='steps-pre')
    elif (ch==5):
        plt.subplot(2,1,2)
        plt.title("Encoded Data Using AMI")
        plt.ylabel("Bits")
        plt.plot(AMI(li),color='green',drawstyle='steps-pre')
    else: 
        print("Wrong choice")
    plt.show()