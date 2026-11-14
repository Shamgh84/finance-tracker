// ---------- تقویم شمسی: تبدیل تاریخ، قالب‌بندی و انتخاب‌گر تاریخ ----------
// الگوریتم تبدیل همان الگوریتمی است که کتابخانه‌ی jdatetime در بک‌اند استفاده می‌کند،
// پس تاریخ‌های مرورگر و سرور با هم یکی‌اند.
const Jalali = (() => {
  const MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
  ];
  const G_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const J_DAYS = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];

  const pad = (n) => String(n).padStart(2, '0');
  const fa = (n) => Number(n).toLocaleString('fa-IR', { useGrouping: false });

  function toJalali(gy, gm, gd) {
    gy -= 1600; gm -= 1; gd -= 1;
    let gDayNo = 365 * gy + Math.floor((gy + 3) / 4)
      - Math.floor((gy + 99) / 100) + Math.floor((gy + 399) / 400);
    for (let i = 0; i < gm; ++i) gDayNo += G_DAYS[i];
    if (gm > 1 && ((gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0)) ++gDayNo;
    gDayNo += gd;

    let jDayNo = gDayNo - 79;
    const jNp = Math.floor(jDayNo / 12053);
    jDayNo %= 12053;
    let jy = 979 + 33 * jNp + 4 * Math.floor(jDayNo / 1461);
    jDayNo %= 1461;
    if (jDayNo >= 366) {
      jy += Math.floor((jDayNo - 1) / 365);
      jDayNo = (jDayNo - 1) % 365;
    }
    let i = 0;
    for (; i < 11 && jDayNo >= J_DAYS[i]; ++i) jDayNo -= J_DAYS[i];
    return { year: jy, month: i + 1, day: jDayNo + 1 };
  }

  function toGregorian(jy, jm, jd) {
    jy -= 979; jm -= 1; jd -= 1;
    let jDayNo = 365 * jy + Math.floor(jy / 33) * 8 + Math.floor(((jy % 33) + 3) / 4);
    for (let i = 0; i < jm; ++i) jDayNo += J_DAYS[i];
    jDayNo += jd;

    let gDayNo = jDayNo + 79;
    let gy = 1600 + 400 * Math.floor(gDayNo / 146097);
    gDayNo %= 146097;
    let leap = true;
    if (gDayNo >= 36525) {
      gDayNo--;
      gy += 100 * Math.floor(gDayNo / 36524);
      gDayNo %= 36524;
      if (gDayNo >= 365) gDayNo++;
      else leap = false;
    }
    gy += 4 * Math.floor(gDayNo / 1461);
    gDayNo %= 1461;
    if (gDayNo >= 366) {
      leap = false;
      gDayNo--;
      gy += Math.floor(gDayNo / 365);
      gDayNo %= 365;
    }
    let i = 0;
    for (; gDayNo >= G_DAYS[i] + (i === 1 && leap ? 1 : 0); i++) {
      gDayNo -= G_DAYS[i] + (i === 1 && leap ? 1 : 0);
    }
    return { year: gy, month: i + 1, day: gDayNo + 1 };
  }

  const fromIso = (iso) => {
    const [y, m, d] = iso.split('-').map(Number);
    return toJalali(y, m, d);
  };

  const toIso = (jy, jm, jd) => {
    const g = toGregorian(jy, jm, jd);
    return `${g.year}-${pad(g.month)}-${pad(g.day)}`;
  };

  function daysInMonth(jy, jm) {
    if (jm <= 6) return 31;
    if (jm <= 11) return 30;
    const g = toGregorian(jy, 12, 30);
    const back = toJalali(g.year, g.month, g.day);
    return back.month === 12 && back.day === 30 ? 30 : 29;
  }

  function monthRange(jy, jm) {
    return { from: toIso(jy, jm, 1), to: toIso(jy, jm, daysInMonth(jy, jm)) };
  }

  function todayIso() {
    const d = new Date();
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  const today = () => fromIso(todayIso());

  // ---------- قالب‌بندی ----------
  const formatJalali = (iso) => {
    const j = fromIso(iso);
    return `${fa(j.day)} ${MONTHS[j.month - 1]} ${fa(j.year)}`;
  };

  const formatGregorian = (iso) => {
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(
      'en-GB', { day: 'numeric', month: 'short', year: 'numeric' }
    );
  };

  const monthTitle = (jy, jm) => `${MONTHS[jm - 1]} ${fa(jy)}`;

  // تاریخ شمسی و زیر آن میلادی (برای جدول‌ها)
  const dual = (iso) =>
    `<div>${formatJalali(iso)}</div><div class="greg-date">${formatGregorian(iso)}</div>`;

  // بازه‌ی میلادی، مثل «23 Oct 2026 – 21 Nov 2026» (برای نمایش در متن فارسی)
  const rangeHtml = (fromIsoValue, toIsoValue) =>
    `<span class="latin">${formatGregorian(fromIsoValue)} – ${formatGregorian(toIsoValue)}</span>`;

  return {
    MONTHS, fa, toJalali, toGregorian, fromIso, toIso, daysInMonth, monthRange,
    today, todayIso, formatJalali, formatGregorian, monthTitle, dual, rangeHtml,
  };
})();


// ---------- انتخاب‌گر تاریخ شمسی (سه لیست: روز، ماه، سال) ----------
// مقدار آن همیشه تاریخ میلادی با قالب YYYY-MM-DD است و زیرش معادل میلادی نمایش داده می‌شود.
const DatePicker = {
  create(container, { optional = false } = {}) {
    container.classList.add('jdate');
    container.innerHTML =
      '<select class="jd-day"></select>' +
      '<select class="jd-month"></select>' +
      '<select class="jd-year"></select>' +
      '<span class="jd-greg muted"></span>';

    const daySel = container.querySelector('.jd-day');
    const monthSel = container.querySelector('.jd-month');
    const yearSel = container.querySelector('.jd-year');
    const greg = container.querySelector('.jd-greg');
    const listeners = [];
    const nowJ = Jalali.today();
    let minYear = nowJ.year - 10;
    let maxYear = nowJ.year + 2;

    function fill(select, items, placeholder) {
      select.innerHTML = '';
      if (placeholder) select.add(new Option(placeholder, ''));
      items.forEach(([value, label]) => select.add(new Option(label, value)));
    }

    function fillYears() {
      const current = yearSel.value;
      const items = [];
      for (let y = minYear; y <= maxYear; y++) items.push([y, Jalali.fa(y)]);
      fill(yearSel, items, optional ? 'سال' : null);
      if (current) yearSel.value = current;
    }

    function fillDays() {
      const year = Number(yearSel.value);
      const month = Number(monthSel.value);
      const count = year && month ? Jalali.daysInMonth(year, month) : 31;
      const current = daySel.value;
      const items = Array.from({ length: count }, (_, i) => [i + 1, Jalali.fa(i + 1)]);
      fill(daySel, items, optional ? 'روز' : null);
      if (current && Number(current) <= count) daySel.value = current;
      else if (current && !optional) daySel.value = String(count);
    }

    function value() {
      const year = Number(yearSel.value);
      const month = Number(monthSel.value);
      const day = Number(daySel.value);
      return year && month && day ? Jalali.toIso(year, month, day) : '';
    }

    function refresh() {
      const iso = value();
      greg.textContent = iso ? `میلادی: ${Jalali.formatGregorian(iso)}` : '';
    }

    function notify() {
      const iso = value();
      listeners.forEach((fn) => fn(iso));
    }

    function set(iso) {
      if (!iso && !optional) iso = Jalali.todayIso();
      if (!iso) {
        yearSel.value = '';
        monthSel.value = '';
        fillDays();
        daySel.value = '';
        refresh();
        return;
      }
      const j = Jalali.fromIso(iso);
      if (j.year < minYear || j.year > maxYear) {
        minYear = Math.min(minYear, j.year);
        maxYear = Math.max(maxYear, j.year);
        fillYears();
      }
      yearSel.value = String(j.year);
      monthSel.value = String(j.month);
      fillDays();
      daySel.value = String(j.day);
      refresh();
    }

    fill(monthSel, Jalali.MONTHS.map((name, i) => [i + 1, name]), optional ? 'ماه' : null);
    fillYears();
    fillDays();
    set(optional ? '' : Jalali.todayIso());

    yearSel.addEventListener('change', () => { fillDays(); refresh(); notify(); });
    monthSel.addEventListener('change', () => { fillDays(); refresh(); notify(); });
    daySel.addEventListener('change', () => { refresh(); notify(); });

    return {
      get value() { return value(); },
      set,
      onChange(fn) { listeners.push(fn); },
    };
  },
};