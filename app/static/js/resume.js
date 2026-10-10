(function () {
  var STORAGE_KEY = "carreirahub:resume:v1";
  var MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

  function emptyResume() {
    return {
      template: "classico",
      personal: { name: "", title: "", email: "", phone: "", city: "", linkedin: "", website: "" },
      summary: "",
      experiences: [],
      education: [],
      skills: [],
      languages: [],
      courses: [],
    };
  }

  var BLANK_ITEMS = {
    experiences: function () {
      return { role: "", company: "", city: "", start: "", end: "", current: false, description: "" };
    },
    education: function () {
      return { course: "", institution: "", start: "", end: "", status: "concluido" };
    },
    languages: function () {
      return { name: "", level: "intermediario" };
    },
    courses: function () {
      return { name: "", institution: "", year: "" };
    },
  };

  function merge(base, saved) {
    var result = emptyResume();
    if (!saved || typeof saved !== "object") return result;
    Object.keys(result).forEach(function (key) {
      if (saved[key] === undefined) return;
      if (Array.isArray(result[key])) {
        result[key] = Array.isArray(saved[key]) ? saved[key] : [];
      } else if (typeof result[key] === "object") {
        result[key] = Object.assign({}, base[key], saved[key]);
      } else {
        result[key] = saved[key];
      }
    });
    return result;
  }

  function formatMonth(value) {
    if (!value) return "";
    var parts = String(value).split("-");
    if (parts.length < 2) return value;
    var month = parseInt(parts[1], 10);
    if (!month || month < 1 || month > 12) return value;
    return MONTHS[month - 1] + "/" + parts[0];
  }

  document.addEventListener("alpine:init", function () {
    window.Alpine.data("resumeBuilder", function () {
      return {
        data: emptyResume(),
        view: "edit",
        skillInput: "",
        savedAt: "",
        storageError: false,
        saveTimer: null,

        educationStatus: {
          concluido: "Concluído",
          cursando: "Cursando",
          trancado: "Trancado",
        },
        languageLevels: {
          basico: "Básico",
          intermediario: "Intermediário",
          avancado: "Avançado",
          fluente: "Fluente",
          nativo: "Nativo",
        },

        init: function () {
          try {
            var raw = window.localStorage.getItem(STORAGE_KEY);
            if (raw) this.data = merge(emptyResume(), JSON.parse(raw));
          } catch (error) {
            this.storageError = true;
          }
          this.$watch("data", this.scheduleSave.bind(this), { deep: true });
        },

        scheduleSave: function () {
          var self = this;
          window.clearTimeout(this.saveTimer);
          this.saveTimer = window.setTimeout(function () {
            try {
              window.localStorage.setItem(STORAGE_KEY, JSON.stringify(self.data));
              var now = new Date();
              self.savedAt =
                String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
              self.storageError = false;
            } catch (error) {
              self.storageError = true;
            }
          }, 400);
        },

        addItem: function (section) {
          this.data[section].push(BLANK_ITEMS[section]());
        },

        removeItem: function (section, index) {
          this.data[section].splice(index, 1);
        },

        moveItem: function (section, index, offset) {
          var target = index + offset;
          var list = this.data[section];
          if (target < 0 || target >= list.length) return;
          var item = list.splice(index, 1)[0];
          list.splice(target, 0, item);
        },

        addSkill: function () {
          var self = this;
          this.skillInput.split(",").forEach(function (raw) {
            var value = raw.trim().slice(0, 60);
            var exists = self.data.skills.some(function (skill) {
              return skill.toLowerCase() === value.toLowerCase();
            });
            if (value && !exists) self.data.skills.push(value);
          });
          this.skillInput = "";
        },

        removeSkill: function (index) {
          this.data.skills.splice(index, 1);
        },

        clearAll: function () {
          if (!window.confirm("Apagar todo o conteúdo do currículo neste navegador?")) return;
          this.data = emptyResume();
          try {
            window.localStorage.removeItem(STORAGE_KEY);
          } catch (error) {
            this.storageError = true;
          }
          this.savedAt = "";
        },

        exportPdf: function () {
          window.print();
        },

        period: function (start, end, current) {
          var from = formatMonth(start);
          var to = current ? "atual" : formatMonth(end);
          if (from && to) return from + " – " + to;
          return from || to;
        },

        bullets: function (text) {
          return String(text || "")
            .split("\n")
            .map(function (line) {
              return line.replace(/^[\s•\-*]+/, "").trim();
            })
            .filter(Boolean);
        },

        contacts: function () {
          var p = this.data.personal;
          return [p.email, p.phone, p.city, p.linkedin, p.website].filter(function (value) {
            return value && value.trim();
          });
        },

        get progress() {
          var d = this.data;
          var checks = [
            d.personal.name,
            d.personal.title,
            d.personal.email || d.personal.phone,
            d.summary,
            d.experiences.length,
            d.education.length,
            d.skills.length,
          ];
          var done = checks.filter(Boolean).length;
          return Math.round((done / checks.length) * 100);
        },

        get isEmpty() {
          var d = this.data;
          return (
            !d.personal.name &&
            !d.personal.title &&
            !d.summary &&
            !d.experiences.length &&
            !d.education.length &&
            !d.skills.length &&
            !d.languages.length &&
            !d.courses.length
          );
        },
      };
    });
  });
})();
