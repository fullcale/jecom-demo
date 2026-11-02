(function(){
  var b=document.body;
  var mb=document.querySelector('.menu-btn');
  if(mb){mb.addEventListener('click',function(){b.classList.toggle('nav-open');mb.setAttribute('aria-expanded',b.classList.contains('nav-open'));});}
  // スマホではメニュー項目タップでサブメニュー開閉
  document.querySelectorAll('.gnav>.item>a').forEach(function(a){
    a.addEventListener('click',function(e){
      if(window.innerWidth>900)return;
      var it=a.parentNode;
      if(it.querySelector('.drop')&&!it.classList.contains('open')){e.preventDefault();it.classList.add('open');}
    });
  });
  var tt=document.querySelector('.to-top');
  window.addEventListener('scroll',function(){if(tt)tt.classList.toggle('show',window.scrollY>600);},{passive:true});
  // スクロールで表示
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{rootMargin:'0px 0px -8% 0px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
  }else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});}
  // 商品ページの写真列（現行の自動スライド）→ スライドショーに
  document.querySelectorAll('.article .gallery').forEach(function(g){
    var imgs=g.querySelectorAll('img');
    if(imgs.length<2)return;
    var s=document.createElement('div');s.className='slider';s.setAttribute('data-auto','3500');
    var sl=document.createElement('div');sl.className='slides';
    imgs.forEach(function(im){var d=document.createElement('div');d.appendChild(im);sl.appendChild(d);});
    s.appendChild(sl);g.parentNode.replaceChild(s,g);
    var first=sl.querySelector('img');
    var setAr=function(){if(first.naturalWidth)s.style.setProperty('--ar',first.naturalWidth+'/'+first.naturalHeight);};
    first.loading='eager';if(first.complete)setAr();else first.addEventListener('load',setAr);
  });
  // スライドショー（自動切り替え・ドット・前後ボタン・ホバーで一時停止）
  document.querySelectorAll('.slider').forEach(function(s){
    var items=s.querySelectorAll('.slides>*');if(items.length<2){if(items[0])items[0].classList.add('on');return;}
    var i=0,timer=null,ms=+(s.getAttribute('data-auto')||5000);
    var dots=document.createElement('div');dots.className='dots';
    items.forEach(function(_,k){var b=document.createElement('button');b.setAttribute('aria-label',(k+1)+'枚目');b.addEventListener('click',function(){go(k);restart();});dots.appendChild(b);});
    s.appendChild(dots);
    ['prev','next'].forEach(function(c){var b=document.createElement('button');b.className='nav '+c;b.setAttribute('aria-label',c==='prev'?'前へ':'次へ');b.textContent=c==='prev'?'‹':'›';b.addEventListener('click',function(){go(i+(c==='prev'?-1:1));restart();});s.appendChild(b);});
    function go(k){items[i].classList.remove('on');dots.children[i].classList.remove('on');i=(k+items.length)%items.length;items[i].classList.add('on');dots.children[i].classList.add('on');}
    function restart(){clearInterval(timer);timer=setInterval(function(){go(i+1);},ms);}
    s.addEventListener('mouseenter',function(){clearInterval(timer);});
    s.addEventListener('mouseleave',restart);
    items.forEach(function(it){it.querySelectorAll('img').forEach(function(im){im.loading='eager';});});
    go(0);restart();
  });
  // デモのフォームは送信しない
  document.querySelectorAll('form.form').forEach(function(f){f.addEventListener('submit',function(e){e.preventDefault();alert('デモサイトのため送信されません。');});});
  // ニュースのアンカー直リンクで該当項目を開く
  if(location.hash){var t=document.getElementById(location.hash.slice(1));if(t&&t.tagName==='DETAILS')t.open=true;}
})();
