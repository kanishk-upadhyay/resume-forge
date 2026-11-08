// Resume Forge Client App - In-House Reactive Resume Studio

let currentResume = {
  basics: {
    name: "Kanishk Upadhyay",
    email: "kanishkupadhyay22@gmail.com",
    phone: "+91 7772034062",
    location: { city: "Bhopal, India" },
    url: "https://kanishk.pages.dev/treasures",
    profiles: [
      { network: "GitHub", url: "https://github.com/kanishk-upadhyay" },
      { network: "GitLab", url: "https://gitlab.com/kanishk0" },
      { network: "LinkedIn", url: "https://linkedin.com/in/kanishk22" }
    ]
  },
  education: [],
  work: [],
  open_source: [],
  projects: [],
  skills: []
};

let currentZoom = 1.0;

document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupSliders();
  setupActionButtons();
  setupZoom();
  await loadInitialSample();
});

function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const targetId = `tab-${btn.dataset.tab}`;
      document.getElementById(targetId)?.classList.add("active");

      if (btn.dataset.tab === "latex") {
        syncFormToLatex();
      }
    });
  });
}

function setupSliders() {
  const rangeFont = document.getElementById("range-font-size");
  const valFont = document.getElementById("val-font-size");
  const rangeLine = document.getElementById("range-line-height");
  const valLine = document.getElementById("val-line-height");
  const rangeMargin = document.getElementById("range-margin");
  const valMargin = document.getElementById("val-margin");

  rangeFont.addEventListener("input", (e) => {
    valFont.textContent = `${e.target.value} pt`;
    renderPreview();
  });

  rangeLine.addEventListener("input", (e) => {
    valLine.textContent = e.target.value;
    renderPreview();
  });

  rangeMargin.addEventListener("input", (e) => {
    valMargin.textContent = `${parseFloat(e.target.value).toFixed(2)} in`;
    renderPreview();
  });
}

function setupActionButtons() {
  // Compile PDF
  document.getElementById("btn-compile-pdf").addEventListener("click", async () => {
    const btn = document.getElementById("btn-compile-pdf");
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Compiling...";
    btn.disabled = true;

    try {
      const resp = await fetch("/api/compile-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume: currentResume,
          font_size: parseFloat(document.getElementById("range-font-size").value),
          line_height: parseFloat(document.getElementById("range-line-height").value),
          margin: parseFloat(document.getElementById("range-margin").value)
        })
      });
      const data = await resp.json();
      if (data.success && data.pdf_url) {
        const a = document.createElement("a");
        a.href = data.pdf_url + "?t=" + Date.now();
        a.download = `${currentResume.basics.name.replace(/\s+/g, "_")}_Resume.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        // Fallback to browser print-to-pdf
        window.print();
      }
    } catch (err) {
      // Offline / Static hosting fallback: Native single-page print
      window.print();
    } finally {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  });

  // Export LaTeX
  document.getElementById("btn-export-latex").addEventListener("click", async () => {
    try {
      const resp = await fetch("/api/generate-tex", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume: currentResume })
      });
      const data = await resp.json();
      downloadFile(`${currentResume.basics.name.replace(/\s+/g, "_")}_resume.tex`, data.latex);
    } catch (err) {
      const tex = window.ClientResumeEngine ? window.ClientResumeEngine.generateLatex(currentResume) : "";
      downloadFile(`${currentResume.basics.name.replace(/\s+/g, "_")}_resume.tex`, tex);
    }
  });

  // Export JSON
  document.getElementById("btn-export-json").addEventListener("click", () => {
    const jsonStr = JSON.stringify(currentResume, null, 2);
    downloadFile("resume.json", jsonStr);
  });

  // Copy ATS Text
  document.getElementById("btn-copy-ats").addEventListener("click", () => {
    let text = `${currentResume.basics.name}\n${currentResume.basics.email} | ${currentResume.basics.phone} | ${currentResume.basics.location?.city || ''}\n\n`;
    
    text += "EXPERIENCE\n";
    currentResume.work.forEach(w => {
      text += `${w.position} - ${w.name} (${w.start_date} - ${w.end_date})\n`;
      (w.highlights || []).forEach(h => text += `• ${h}\n`);
      text += "\n";
    });

    text += "EDUCATION\n";
    currentResume.education.forEach(e => {
      text += `${e.institution} - ${e.study_type} (${e.start_date} - ${e.end_date})\n`;
      (e.highlights || []).forEach(h => text += `• ${h}\n`);
      text += "\n";
    });

    text += "PROJECTS\n";
    currentResume.projects.forEach(p => {
      text += `${p.name} [${(p.keywords || []).join(", ")}]\n`;
      (p.highlights || []).forEach(h => text += `• ${h}\n`);
      text += "\n";
    });

    text += "SKILLS\n";
    currentResume.skills.forEach(s => {
      text += `${s.name}: ${(s.keywords || []).join(", ")}\n`;
    });

    navigator.clipboard.writeText(text);
    alert("Copied clean plain text for ATS application forms!");
  });

  // Parse TeX to Form
  document.getElementById("btn-parse-tex-to-form").addEventListener("click", async () => {
    const rawTex = document.getElementById("latex-editor").value;
    try {
      const resp = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latex: rawTex })
      });
      const data = await resp.json();
      if (data.resume) {
        currentResume = data.resume;
        populateForm();
        renderPreview();
        alert(`Parsed successfully: ${data.summary.jobs} jobs, ${data.summary.projects} projects, ${data.summary.skills} skill categories!`);
        return;
      }
    } catch (err) {
      // Fallback to client-side engine
      if (window.ClientResumeEngine) {
        const parsed = window.ClientResumeEngine.parseLatex(rawTex);
        currentResume = parsed;
        populateForm();
        renderPreview();
        alert(`Parsed offline: ${parsed.work.length} jobs, ${parsed.projects.length} projects, ${parsed.skills.length} skill categories!`);
      }
    }
  });

  // Load CERN Sample
  document.getElementById("btn-load-cern").addEventListener("click", loadInitialSample);

  // ATS Audit
  document.getElementById("btn-run-audit").addEventListener("click", async () => {
    const jd = document.getElementById("jd-input").value;
    try {
      const resp = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume: currentResume, job_description: jd })
      });
      const audit = await resp.json();
      renderAudit(audit);
    } catch (err) {
      if (window.ClientResumeEngine) {
        const audit = window.ClientResumeEngine.auditResume(currentResume, jd);
        renderAudit(audit);
      }
    }
  });
    const audit = await resp.json();
    renderAudit(audit);
  });

  // Form inputs listener
  ["inp-name", "inp-email", "inp-phone", "inp-location", "inp-website"].forEach(id => {
    document.getElementById(id).addEventListener("input", () => {
      currentResume.basics.name = document.getElementById("inp-name").value;
      currentResume.basics.email = document.getElementById("inp-email").value;
      currentResume.basics.phone = document.getElementById("inp-phone").value;
      currentResume.basics.location.city = document.getElementById("inp-location").value;
      currentResume.basics.url = document.getElementById("inp-website").value;
      renderPreview();
    });
  });

  // Dynamic Add Buttons
  document.getElementById("btn-add-work").addEventListener("click", () => {
    currentResume.work.unshift({
      name: "Company Name",
      position: "Software Engineer",
      location: "Remote",
      start_date: "2025",
      end_date: "Present",
      highlights: ["Engineered scalable backend services..."]
    });
    populateForm();
    renderPreview();
  });

  document.getElementById("btn-add-edu").addEventListener("click", () => {
    currentResume.education.push({
      institution: "University Name",
      study_type: "B.S. in Computer Science",
      start_date: "2023",
      end_date: "2027",
      highlights: []
    });
    populateForm();
    renderPreview();
  });

  document.getElementById("btn-add-project").addEventListener("click", () => {
    currentResume.projects.push({
      name: "New Project",
      keywords: ["Python", "React"],
      start_date: "2025",
      highlights: ["Built high-impact application..."]
    });
    populateForm();
    renderPreview();
  });

  document.getElementById("btn-add-skill").addEventListener("click", () => {
    currentResume.skills.push({
      name: "Tools & Frameworks",
      keywords: ["Git", "Docker", "Linux"]
    });
    populateForm();
    renderPreview();
  });
}

function setupZoom() {
  document.getElementById("btn-zoom-in").addEventListener("click", () => {
    currentZoom = Math.min(1.5, currentZoom + 0.1);
    applyZoom();
  });
  document.getElementById("btn-zoom-out").addEventListener("click", () => {
    currentZoom = Math.max(0.6, currentZoom - 0.1);
    applyZoom();
  });
}

function applyZoom() {
  document.getElementById("resume-paper").style.transform = `scale(${currentZoom})`;
  document.getElementById("zoom-level").textContent = `${Math.round(currentZoom * 100)}%`;
}

async function loadInitialSample() {
  try {
    const resp = await fetch("/api/sample");
    const data = await resp.json();
    if (data.resume) {
      currentResume = data.resume;
      document.getElementById("latex-editor").value = data.latex || "";
      populateForm();
      renderPreview();
    }
  } catch (err) {
    console.warn("Failed to load sample, using default state", err);
    populateForm();
    renderPreview();
  }
}

function populateForm() {
  const b = currentResume.basics || {};
  document.getElementById("inp-name").value = b.name || "";
  document.getElementById("inp-email").value = b.email || "";
  document.getElementById("inp-phone").value = b.phone || "";
  document.getElementById("inp-location").value = b.location?.city || "";
  document.getElementById("inp-website").value = b.url || "";

  renderWorkList();
  renderEduList();
  renderOSList();
  renderProjectList();
  renderSkillList();
}

function renderWorkList() {
  const container = document.getElementById("work-items-container");
  container.innerHTML = "";
  (currentResume.work || []).forEach((w, idx) => {
    const box = document.createElement("div");
    box.className = "item-box";
    box.innerHTML = `
      <div class="item-box-header">
        <span class="item-box-title">${w.position || "Position"} @ ${w.name || "Company"}</span>
        <button class="btn-del" onclick="deleteWork(${idx})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Role</label><input type="text" value="${w.position || ""}" oninput="updateWork(${idx}, 'position', this.value)"></div>
        <div class="form-group"><label>Company</label><input type="text" value="${w.name || ""}" oninput="updateWork(${idx}, 'name', this.value)"></div>
        <div class="form-group"><label>Dates</label><input type="text" value="${w.start_date} – ${w.end_date}" oninput="updateWorkDates(${idx}, this.value)"></div>
        <div class="form-group"><label>Location</label><input type="text" value="${w.location || ""}" oninput="updateWork(${idx}, 'location', this.value)"></div>
      </div>
      <div class="bullets-box">
        <label>Bullet Points (Impact & Outcomes)</label>
        ${(w.highlights || []).map((h, hIdx) => `
          <div class="bullet-row">
            <textarea rows="2" oninput="updateWorkBullet(${idx}, ${hIdx}, this.value)">${h}</textarea>
            <button class="btn-del" onclick="deleteWorkBullet(${idx}, ${hIdx})">✕</button>
          </div>
        `).join("")}
        <button class="btn-sm btn-outline" onclick="addWorkBullet(${idx})">+ Add Bullet</button>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderEduList() {
  const container = document.getElementById("edu-items-container");
  container.innerHTML = "";
  (currentResume.education || []).forEach((e, idx) => {
    const box = document.createElement("div");
    box.className = "item-box";
    box.innerHTML = `
      <div class="item-box-header">
        <span class="item-box-title">${e.institution || "Institution"}</span>
        <button class="btn-del" onclick="deleteEdu(${idx})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Institution</label><input type="text" value="${e.institution || ""}" oninput="updateEdu(${idx}, 'institution', this.value)"></div>
        <div class="form-group"><label>Degree / Major</label><input type="text" value="${e.study_type || ""}" oninput="updateEdu(${idx}, 'study_type', this.value)"></div>
        <div class="form-group"><label>Dates</label><input type="text" value="${e.start_date} – ${e.end_date}" oninput="updateEduDates(${idx}, this.value)"></div>
        <div class="form-group"><label>Location</label><input type="text" value="${e.area || ""}" oninput="updateEdu(${idx}, 'area', this.value)"></div>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderOSList() {
  const container = document.getElementById("os-items-container");
  container.innerHTML = "";
  (currentResume.open_source || []).forEach((os, idx) => {
    const box = document.createElement("div");
    box.className = "item-box";
    box.innerHTML = `
      <div class="item-box-header">
        <span class="item-box-title">${os.project || "Project"}</span>
        <button class="btn-del" onclick="deleteOS(${idx})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Project / Ecosystem</label><input type="text" value="${os.project || ""}" oninput="updateOS(${idx}, 'project', this.value)"></div>
        <div class="form-group"><label>Role / Scope</label><input type="text" value="${os.role || ""}" oninput="updateOS(${idx}, 'role', this.value)"></div>
      </div>
      <div class="bullets-box">
        ${(os.highlights || []).map((h, hIdx) => `
          <div class="bullet-row">
            <textarea rows="2" oninput="updateOSBullet(${idx}, ${hIdx}, this.value)">${h}</textarea>
            <button class="btn-del" onclick="deleteOSBullet(${idx}, ${hIdx})">✕</button>
          </div>
        `).join("")}
        <button class="btn-sm btn-outline" onclick="addOSBullet(${idx})">+ Add Bullet</button>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderProjectList() {
  const container = document.getElementById("project-items-container");
  container.innerHTML = "";
  (currentResume.projects || []).forEach((p, idx) => {
    const box = document.createElement("div");
    box.className = "item-box";
    box.innerHTML = `
      <div class="item-box-header">
        <span class="item-box-title">${p.name || "Project"}</span>
        <button class="btn-del" onclick="deleteProject(${idx})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Project Name</label><input type="text" value="${p.name || ""}" oninput="updateProject(${idx}, 'name', this.value)"></div>
        <div class="form-group"><label>Tech Stack (comma-separated)</label><input type="text" value="${(p.keywords || []).join(', ')}" oninput="updateProjectKeywords(${idx}, this.value)"></div>
        <div class="form-group"><label>Dates</label><input type="text" value="${p.start_date || ""}" oninput="updateProject(${idx}, 'start_date', this.value)"></div>
        <div class="form-group"><label>Live URL</label><input type="url" value="${p.url || ""}" oninput="updateProject(${idx}, 'url', this.value)"></div>
      </div>
      <div class="bullets-box">
        ${(p.highlights || []).map((h, hIdx) => `
          <div class="bullet-row">
            <textarea rows="2" oninput="updateProjectBullet(${idx}, ${hIdx}, this.value)">${h}</textarea>
            <button class="btn-del" onclick="deleteProjectBullet(${idx}, ${hIdx})">✕</button>
          </div>
        `).join("")}
        <button class="btn-sm btn-outline" onclick="addProjectBullet(${idx})">+ Add Bullet</button>
      </div>
    `;
    container.appendChild(box);
  });
}

function renderSkillList() {
  const container = document.getElementById("skill-items-container");
  container.innerHTML = "";
  (currentResume.skills || []).forEach((s, idx) => {
    const box = document.createElement("div");
    box.className = "item-box";
    box.innerHTML = `
      <div class="item-box-header">
        <span class="item-box-title">${s.name || "Category"}</span>
        <button class="btn-del" onclick="deleteSkill(${idx})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Category Name</label><input type="text" value="${s.name || ""}" oninput="updateSkill(${idx}, 'name', this.value)"></div>
        <div class="form-group"><label>Skills (comma-separated)</label><input type="text" value="${(s.keywords || []).join(', ')}" oninput="updateSkillKeywords(${idx}, this.value)"></div>
      </div>
    `;
    container.appendChild(box);
  });
}

// Global update handlers for form inputs
window.updateWork = (idx, field, val) => { currentResume.work[idx][field] = val; renderPreview(); };
window.updateWorkDates = (idx, val) => { const parts = val.split(/[–—\-]/); currentResume.work[idx].start_date = parts[0]?.trim(); currentResume.work[idx].end_date = parts[1]?.trim(); renderPreview(); };
window.updateWorkBullet = (idx, hIdx, val) => { currentResume.work[idx].highlights[hIdx] = val; renderPreview(); };
window.addWorkBullet = (idx) => { currentResume.work[idx].highlights.push("Accomplished X by implementing Y..."); renderWorkList(); renderPreview(); };
window.deleteWorkBullet = (idx, hIdx) => { currentResume.work[idx].highlights.splice(hIdx, 1); renderWorkList(); renderPreview(); };
window.deleteWork = (idx) => { currentResume.work.splice(idx, 1); renderWorkList(); renderPreview(); };

window.updateEdu = (idx, field, val) => { currentResume.education[idx][field] = val; renderPreview(); };
window.updateEduDates = (idx, val) => { const parts = val.split(/[–—\-]/); currentResume.education[idx].start_date = parts[0]?.trim(); currentResume.education[idx].end_date = parts[1]?.trim(); renderPreview(); };
window.deleteEdu = (idx) => { currentResume.education.splice(idx, 1); renderEduList(); renderPreview(); };

window.updateOS = (idx, field, val) => { currentResume.open_source[idx][field] = val; renderPreview(); };
window.updateOSBullet = (idx, hIdx, val) => { currentResume.open_source[idx].highlights[hIdx] = val; renderPreview(); };
window.addOSBullet = (idx) => { currentResume.open_source[idx].highlights.push("Contributed..."); renderOSList(); renderPreview(); };
window.deleteOSBullet = (idx, hIdx) => { currentResume.open_source[idx].highlights.splice(hIdx, 1); renderOSList(); renderPreview(); };
window.deleteOS = (idx) => { currentResume.open_source.splice(idx, 1); renderOSList(); renderPreview(); };

window.updateProject = (idx, field, val) => { currentResume.projects[idx][field] = val; renderPreview(); };
window.updateProjectKeywords = (idx, val) => { currentResume.projects[idx].keywords = val.split(',').map(s => s.trim()).filter(Boolean); renderPreview(); };
window.updateProjectBullet = (idx, hIdx, val) => { currentResume.projects[idx].highlights[hIdx] = val; renderPreview(); };
window.addProjectBullet = (idx) => { currentResume.projects[idx].highlights.push("Engineered feature..."); renderProjectList(); renderPreview(); };
window.deleteProjectBullet = (idx, hIdx) => { currentResume.projects[idx].highlights.splice(hIdx, 1); renderProjectList(); renderPreview(); };
window.deleteProject = (idx) => { currentResume.projects.splice(idx, 1); renderProjectList(); renderPreview(); };

window.updateSkill = (idx, field, val) => { currentResume.skills[idx][field] = val; renderPreview(); };
window.updateSkillKeywords = (idx, val) => { currentResume.skills[idx].keywords = val.split(',').map(s => s.trim()).filter(Boolean); renderPreview(); };
window.deleteSkill = (idx) => { currentResume.skills.splice(idx, 1); renderSkillList(); renderPreview(); };

function renderPreview() {
  const paper = document.getElementById("resume-paper");
  const fontSize = parseFloat(document.getElementById("range-font-size").value);
  const lineHeight = parseFloat(document.getElementById("range-line-height").value);
  const margin = parseFloat(document.getElementById("range-margin").value);

  paper.style.fontSize = `${fontSize}pt`;
  paper.style.lineHeight = lineHeight;
  paper.style.padding = `${margin}in`;

  const b = currentResume.basics || {};
  const contactParts = [];
  if (b.phone) contactParts.push(`<span>${b.phone}</span>`);
  if (b.email) contactParts.push(`<a href="mailto:${b.email}">${b.email}</a>`);
  if (b.location?.city) contactParts.push(`<span>${b.location.city}</span>`);
  if (b.url) contactParts.push(`<a href="${b.url}" target="_blank">${b.url.replace(/^https?:\/\//, '')}</a>`);
  (b.profiles || []).forEach(p => {
    contactParts.push(`<a href="${p.url}" target="_blank">${p.url.replace(/^https?:\/\//, '')}</a>`);
  });

  let html = `
    <header>
      <h1>${b.name || "Candidate Name"}</h1>
      <div class="contact-line">${contactParts.join(" | ")}</div>
    </header>
  `;

  // Education
  if (currentResume.education?.length) {
    html += `<div class="section-header">Education</div>`;
    currentResume.education.forEach(e => {
      const dates = e.end_date ? `${e.start_date} – ${e.end_date}` : e.start_date;
      html += `
        <div class="entry-row">
          <div class="entry-title">${e.institution}</div>
          <div class="entry-date">${dates || ""}</div>
        </div>
        <div class="entry-row">
          <div class="entry-subtitle">${e.study_type || ""}</div>
          <div class="entry-location">${e.area || ""}</div>
        </div>
      `;
      if (e.highlights?.length) {
        html += `<ul class="entry-bullets">`;
        e.highlights.forEach(h => html += `<li>${h}</li>`);
        html += `</ul>`;
      }
    });
  }

  // Work Experience
  if (currentResume.work?.length) {
    html += `<div class="section-header">Experience</div>`;
    currentResume.work.forEach(w => {
      const dates = w.end_date ? `${w.start_date} – ${w.end_date}` : w.start_date;
      html += `
        <div class="entry-row">
          <div class="entry-title">${w.position}</div>
          <div class="entry-date">${dates || ""}</div>
        </div>
        <div class="entry-row">
          <div class="entry-subtitle">${w.name}</div>
          <div class="entry-location">${w.location || ""}</div>
        </div>
      `;
      if (w.highlights?.length) {
        html += `<ul class="entry-bullets">`;
        w.highlights.forEach(h => html += `<li>${h}</li>`);
        html += `</ul>`;
      }
    });
  }

  // Open Source
  if (currentResume.open_source?.length) {
    html += `<div class="section-header">Open-Source Contributions</div>`;
    currentResume.open_source.forEach(os => {
      html += `
        <div class="entry-row">
          <div class="entry-title">${os.project}</div>
          <div class="entry-subtitle">${os.role || ""}</div>
        </div>
      `;
      if (os.highlights?.length) {
        html += `<ul class="entry-bullets">`;
        os.highlights.forEach(h => html += `<li>${h}</li>`);
        html += `</ul>`;
      }
    });
  }

  // Projects
  if (currentResume.projects?.length) {
    html += `<div class="section-header">Projects</div>`;
    currentResume.projects.forEach(p => {
      const techStr = p.keywords?.length ? ` | <em>${p.keywords.join(", ")}</em>` : "";
      html += `
        <div class="entry-row">
          <div class="entry-title">${p.name}${techStr}</div>
          <div class="entry-date">${p.start_date || ""}</div>
        </div>
      `;
      if (p.highlights?.length) {
        html += `<ul class="entry-bullets">`;
        p.highlights.forEach(h => html += `<li>${h}</li>`);
        html += `</ul>`;
      }
    });
  }

  // Skills
  if (currentResume.skills?.length) {
    html += `<div class="section-header">Technical Skills</div>`;
    currentResume.skills.forEach(s => {
      html += `
        <div class="skill-row">
          <span class="skill-category">${s.name}:</span> ${(s.keywords || []).join(", ")}
        </div>
      `;
    });
  }

  paper.innerHTML = html;

  // Single-page budget detection
  // 11 inches at 96 DPI is 1056px
  setTimeout(checkPageBudget, 30);
}

function checkPageBudget() {
  const paper = document.getElementById("resume-paper");
  const actualHeight = paper.scrollHeight;
  const targetSinglePageHeight = 1056; // 11in at 96dpi

  const pct = Math.round((actualHeight / targetSinglePageHeight) * 100);
  const pill = document.getElementById("page-budget-pill");
  const text = document.getElementById("page-budget-text");

  pill.className = "pill";
  if (pct <= 100) {
    pill.classList.add("pill-good");
    text.textContent = `Page Budget: ${pct}% (Single Page - Optimal)`;
  } else if (pct <= 108) {
    pill.classList.add("pill-warn");
    text.textContent = `Page Budget: ${pct}% (Borderline Overflow)`;
  } else {
    pill.classList.add("pill-danger");
    text.textContent = `Page Budget: ${pct}% (⚠️ Spills to Page 2)`;
  }
}

async function syncFormToLatex() {
  try {
    const resp = await fetch("/api/generate-tex", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume: currentResume })
    });
    const data = await resp.json();
    if (data.latex) {
      document.getElementById("latex-editor").value = data.latex;
    }
  } catch (err) {
    if (window.ClientResumeEngine) {
      document.getElementById("latex-editor").value = window.ClientResumeEngine.generateLatex(currentResume);
    }
  }
}

function renderAudit(audit) {
  const resDiv = document.getElementById("ats-results");
  resDiv.style.display = "block";

  document.getElementById("ats-score-num").textContent = audit.score;
  document.getElementById("ats-page-status").textContent = `Page Budget: ${audit.page_budget_percent}% (${audit.page_status})`;

  const strengthsList = document.getElementById("ats-strengths");
  strengthsList.innerHTML = audit.strengths.map(s => `<li>${s}</li>`).join("");

  const suggList = document.getElementById("ats-suggestions");
  suggList.innerHTML = audit.suggestions.map(s => `<li>${s}</li>`).join("");

  const tagCloud = document.getElementById("ats-keywords-matched");
  if (audit.matched_keywords?.length) {
    tagCloud.innerHTML = audit.matched_keywords.map(k => `<span class="tag-badge">${k}</span>`).join("");
  } else {
    tagCloud.innerHTML = "<span style='font-size:11px; color:#94a3b8;'>Paste a job description above to match keywords.</span>";
  }
}

function downloadFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
