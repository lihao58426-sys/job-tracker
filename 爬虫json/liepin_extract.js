/**
 * 猎聘列表页岗位提取脚本
 *
 * 用法：导航到猎聘搜索页（https://www.liepin.com/zhaopin/?key=关键词）后，
 *       在浏览器 console 或 playwright MCP 的 evaluate / save_result 中运行本函数。
 * 返回：当前页所有岗位的 10 字段数组（已过滤 title/company/url 非空的记录）。
 *
 * 注意：本脚本只提取"当前页"（约 42 条）。每个关键词需要单独导航 + 单独运行。
 */
(() => {
  const cards = [...document.querySelectorAll('.job-card-pc-container')];

  const data = cards.map((card) => {
    // ── 岗位信息块 ──
    const jobA = card.querySelector('a[data-nick="job-detail-job-info"]');
    const url = jobA ? jobA.href.split('?')[0] : '';

    // title：第一个带 title 属性的 div.ellipsis-1
    const titleEl = jobA ? jobA.querySelector('div.ellipsis-1[title]') : null;
    const title = titleEl ? titleEl.textContent.trim() : '';

    // 岗位信息块结构：第 0 个子 div = 标题+地点+薪资；第 1 个子 div = 经验/学历标签
    const firstDiv = jobA ? jobA.children[0] : null;
    const tagDiv = jobA ? jobA.children[1] : null;

    // location：firstDiv 内的 span.ellipsis-1（【】包裹的那个）
    const locEl = firstDiv ? firstDiv.querySelector('span.ellipsis-1') : null;
    const location = locEl ? locEl.textContent.trim() : '';

    // salary：firstDiv 内文本含 k/元/薪/万 的 span
    const salaryEl = firstDiv
      ? [...firstDiv.querySelectorAll('span')].find((s) => /(k|元|薪|万)/.test(s.textContent))
      : null;
    const salary = salaryEl ? salaryEl.textContent.trim() : '';

    // experience / education：标签区所有 span，第一个=经验，最后一个=学历
    const tags = tagDiv
      ? [...tagDiv.querySelectorAll('span')].map((s) => s.textContent.trim()).filter(Boolean)
      : [];
    const experience = tags[0] || '';
    const education = tags[tags.length - 1] || '';

    // ── 公司信息块 ──
    const compInfo = card.querySelector('div[data-nick="job-detail-company-info"]');
    const company = compInfo
      ? compInfo.querySelector('span.ellipsis-1')?.textContent.trim()
      : '';

    // 行业/融资/规模：3 个 span，按文本特征分类（不能按位置，缺字段时会错位）
    const infoTexts = compInfo
      ? [...compInfo.querySelectorAll('div.ellipsis-1 span')]
          .map((s) => s.textContent.trim())
          .filter(Boolean)
      : [];
    let industry = '';
    let funding = '';
    let scale = '';
    for (const t of infoTexts) {
      if (/人/.test(t) && /\d/.test(t)) scale = t;          // 规模：含"人"且含数字
      else if (/上市|融资|轮/.test(t)) funding = t;          // 融资：含"上市/融资/轮"
      else industry = t;                                     // 行业：其余
    }

    return {
      title,
      salary,
      location,
      company,
      industry,
      funding,
      scale,
      experience,
      education,
      url,
    };
  });

  // 校验：title / company / url 三者必须非空
  return data.filter((j) => j.title && j.company && j.url);
})();
