from io import open_code
import os
from django.http import response
from django.shortcuts import redirect, render
import board
from board.models import Board, Comment
from django.views.decorators.csrf import csrf_exempt
#from django.utils.http import urlquote
from django.http import HttpResponse
from django.db.models import Q
import math

UPLOAD_DIR = 'd:/upload/'

@csrf_exempt
def list(request):

    #검색옵션과 검색키워드
    try:
        search_option = request.POST['search_option']
    except:
        search_option = 'writer'

    try:
        search = request.POST['search']
    except:
        search = ''

    boardCount = Board.objects.count()

    #페이지 나누기 코드
    try:
        start = int(request.GET['start'])  #시작 레코드의 인덱스 값
    except:
        start = 1

    print('start = ', start)

    page_size = 10        #한 페이지에 표시할 게시물 수
    page_list_size = 10   #한 화면에 표시할 페이지 수

    end = start + page_size - 1
    print('end = ', end)

    total_page = math.ceil(boardCount / page_size)   #전체 페이지 갯수, 올림
    print('total_page = ', total_page)
    current_page = math.ceil( (start + 1) / page_size ) #현재 페이지 번호
    print('current_page = ', current_page)

    start_page = math.floor( (current_page + 1) / page_list_size ) * page_list_size #시작 페이지번호
    print('start_page = ', start_page)

    end_page = start_page + page_list_size  #끝 페이지번호
    print('end_page = ', end_page)

    if total_page < end_page:
        end_page = total_page

    if start_page >= page_list_size:    #이전 페이지 표시 로직
        prev_list = (start_page - 1) * page_size
    else:
        prev_list = 0

    print('prev_list', prev_list)

    if total_page > end_page:           #다음 페이지 표시 로직
        next_list = end_page * page_size
    else:
        next_list = 0
    print('next_list', next_list)
    

    if search_option == 'all':
        boardList = Board.objects.filter( Q(writer__contains=search)|Q(title__contains=search)|Q(content__contains=search)).order_by('-idx')[start:end]
    elif search_option == 'writer':
        boardList = Board.objects.filter( Q(writer__contains=search)).order_by('-idx')[start:end]
    elif search_option == 'title':
        boardList = Board.objects.filter( Q(title__contains=search)).order_by('-idx')[start:end]
    elif search_option == 'content':
        boardList = Board.objects.filter( Q(content__contains=search)).order_by('-idx')[start:end]

    #페이지 나누기 링크
    links = []
    for i in range(start_page +1 , end_page + 1):
        page = i* page_size
        links.append("<a href='?start=" + str(page) + "'>" + str(i) + "</a>")

    print(links)
    print('start = ', start)


    return render(request, 'list.html', { 'boardList':boardList, 'boardCount':len(boardList),
                  'search_option': search_option, 'search':search,
                  'range':range(start_page - 1, end_page), 'start_page':start_page,
                  'end_page':end_page, 'page_list_size':page_list_size,
                  'total_page':total_page, 'prev_list':prev_list, 'next_list':next_list,
                  'links':links} )

def write(request):
    return render(request, 'write.html')

@csrf_exempt
def insert(request):
    fname = ''
    fsize = 0
    if 'file' in request.FILES:           #여러 첨부파일의 배열 들중 form에서 name속성을 file로 지정한 것이 있는가
        file = request.FILES['file']
        fname = file._name
        with open('%s%s' %(UPLOAD_DIR, fname), 'wb') as fp:
            for chunk in file.chunks():   #보낼때 multipart로 보내서 chunks라는 조각들이 생김
                fp.write(chunk)
        fsize = os.path.getsize(UPLOAD_DIR + fname)
        row = Board(writer=request.POST['writer'], title=request.POST['title'], content=request.POST['content'],
                    filename = fname, filesize = fsize)
        row.save()
        return redirect('/')

@csrf_exempt
def detail(request):
    id = request.GET['idx']
    row = Board.objects.get(idx=id)
    row.hit_up()
    row.save()
    filesize = '%.2f' %(row.filesize / 1024)

    #댓글 목록
    commentList = Comment.objects.filter(board_idx = id).order_by('idx')
    return render(request, 'detail.html', {'row':row, 'filesize':filesize, 'commentList':commentList})

def update(request):
    id = request.POST['idx']
    row_src = Board.objects.get(idx = id)
    fname = row_src.filename
    fsize = row_src.filesize
    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file._name
        with open('%s%s' % (UPLOAD_DIR, fname), 'wb') as fp:
            for chunk in file.chunk():
                fp.write(chunk)
        fsize = os.path.getsize(UPLOAD_DIR + fname)

    #insert와 다른점은 앞에 idx가 있다는 점이다.
    row_new = Board(idx=id, writer = request.POST['writer'], title = request.POST['title'],
                    content = request.POST['content'], filename = fname, filesize = fsize)
    row_new.save()
    return redirect('/')

def delete(request):
    id = request.POST['idx']
    Board.objects.get(idx=id).delete()
    return redirect('/')

def download(request):
    id = request.GET['idx']
    row = Board.objects.get(idx=id)
    path = UPLOAD_DIR + row.filename
    filename = os.path.basename(path)    # 디렉토리를 제외할 파일이름
    # filename = urlquote(filename)        # 한글/특수문자 인코딩 처리
    with open(path, 'rb') as file:
        #서버의 파일을 읽음, content_type 파일의 종류
        response = HttpResponse(file.read(), content_type='application/octet-stream')  #범용적으로 쓰이는것이 octet-stream
        #response['Content_Disposition'] = "attachment;filename*=UTF-8''{0}".format(filename)  #첨부파일정보 attchment가 맞는지?
        response['Content_Disposition'] = filename
        row.down_up()
        row.save
        return response

@csrf_exempt
def reply_insert(request):
    id = request.POST['idx']
    row = Comment(board_idx = id, writer = request.POST['writer'], content=request.POST['content'])
    row.save()
    return response.HttpResponseRedirect('../detail?idx=' + id)

