var intro = introJs();

intro.setOption("nextLabel", "Далее&rarr;");
intro.setOption("prevLabel", "&larr;Назад");
intro.setOption("skipLabel", "Отмена");
intro.setOption("doneLabel", "Готово");
intro.setOption("showStepNumbers", false);

function startIntro(){
    if (typeof(modIntro) === 'function') {
        modIntro();
    } else{
        intro.setOptions({
        steps: [
            {
                element: '#cur_modules',
                intro: "Перечень доступных модулей",
                position: 'right'
            },
            {
                element: '#users',
                intro: "Управление пользователями, имеющими доступ в панель администрирования ЛПУ",
                position: 'right'
            },
            {
                element: '#gen_settings',
                intro: "Общие настройки, такие как: <ul><li>инфис-код ЛПУ</li><li>устаревший инфис-код ЛПУ</li></ul>",
                position: 'right'
            },
            {
                element: '#logout',
                intro: "Выход из системы (logout)",
                position: 'right'
            }
        ]
      });
    }
  intro.start();
}