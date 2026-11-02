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
  // デモのフォームは送信しない
  document.querySelectorAll('form.form').forEach(function(f){f.addEventListener('submit',function(e){e.preventDefault();alert('デモサイトのため送信されません。');});});
  // ニュースのアンカー直リンクで該当項目を開く
  if(location.hash){var t=document.getElementById(location.hash.slice(1));if(t&&t.tagName==='DETAILS')t.open=true;}
})();
