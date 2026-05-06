document.addEventListener("DOMContentLoaded", () => {
  document.documentElement.style.scrollBehavior = "smooth";
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const sidebarOverlay = document.querySelector("[data-sidebar-overlay]");
  const sidebarLinks = document.querySelectorAll("[data-sidebar] a, [data-sidebar] button");

  const closeSidebar = () => {
    document.body.classList.remove("sidebar-open");
    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", "false");
    }
  };

  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      const willOpen = !document.body.classList.contains("sidebar-open");
      document.body.classList.toggle("sidebar-open", willOpen);
      sidebarToggle.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
  }

  sidebarLinks.forEach((node) => {
    node.addEventListener("click", () => {
      if (window.matchMedia("(max-width: 900px)").matches) {
        closeSidebar();
      }
    });
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSidebar();
    }
  });

  const revealNodes = Array.from(document.querySelectorAll(".reveal"));
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.1 }
    );

    revealNodes.forEach((node, idx) => {
      node.style.transitionDelay = `${Math.min(idx * 60, 360)}ms`;
      observer.observe(node);
    });
  } else {
    revealNodes.forEach((node) => node.classList.add("visible"));
  }

  document.querySelectorAll(".progress-fill[data-progress]").forEach((node) => {
    const progress = Number(node.dataset.progress || "0");
    const safeValue = Math.max(0, Math.min(progress, 100));
    window.setTimeout(() => {
      node.style.width = `${safeValue}%`;
    }, 180);
  });

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const targetId = button.dataset.targetId;
    const targetInput = targetId ? document.getElementById(targetId) : null;
    if (!targetInput) {
      return;
    }

    const openIcon = button.querySelector(".password-icon-open");
    const closedIcon = button.querySelector(".password-icon-closed");

    const syncPasswordToggleState = () => {
      const showingPassword = targetInput.type === "text";
      button.setAttribute("aria-label", showingPassword ? "Hide password" : "Show password");
      button.setAttribute("aria-pressed", showingPassword ? "true" : "false");
      openIcon?.classList.toggle("hidden", showingPassword);
      closedIcon?.classList.toggle("hidden", !showingPassword);
    };

    button.addEventListener("click", () => {
      targetInput.type = targetInput.type === "password" ? "text" : "password";
      syncPasswordToggleState();
    });

    syncPasswordToggleState();
  });

  if (window.dashboardData && Array.isArray(window.dashboardData.charts) && window.Chart) {
    const formatMetricValue = (value, chart, datasetLabel = "") => {
      if (value === null || value === undefined) {
        return "";
      }

      const isPercent = chart.value_is_percent || datasetLabel.includes("%");
      const isPrice = datasetLabel.toLowerCase().includes("price");
      if (isPercent) {
        return `${Number(value).toFixed(1)}%`;
      }
      if (isPrice) {
        return `Rs. ${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      }
      return Number(value).toLocaleString();
    };

    const buildChartOptions = (chart) => {
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: "index",
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              usePointStyle: true,
              padding: 18,
            },
          },
          tooltip: {
            backgroundColor: "rgba(54, 37, 27, 0.94)",
            titleColor: "#fff8f2",
            bodyColor: "#fff8f2",
            padding: 12,
            callbacks: {
              title: (items) => {
                if (!items.length) {
                  return "";
                }
                const item = items[0];
                if (chart.tooltip_mode === "bubble_price_volume") {
                  return item.dataset.label || "Category";
                }
                return item.label || "";
              },
              label: (context) => {
                if (chart.tooltip_mode === "bubble_price_volume") {
                  const point = context.raw || {};
                  return [
                    `Average Price: Rs. ${Number(point.x || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                    `Average Units Sold: ${Number(point.y || 0).toLocaleString()}`,
                    "Bubble size is a visual marker.",
                  ];
                }

                if (chart.tooltip_mode === "dual_metric") {
                  const datasetLabel = context.dataset.label || "";
                  const label = datasetLabel.includes("Price") ? chart.right_metric_label : chart.left_metric_label;
                  return `${label}: ${formatMetricValue(context.raw, chart, datasetLabel)}`;
                }

                if (chart.tooltip_mode === "seasonality_compare") {
                  return `${context.dataset.label}: ${Number(context.raw || 0).toLocaleString()} units`;
                }

                return `${context.dataset.label || chart.metric_label || "Value"}: ${formatMetricValue(context.raw, chart, context.dataset.label || "")}`;
              },
            },
          },
        },
      };

      if (chart.axes && chart.axes.secondary_percent) {
        options.scales = {
          y: {
            beginAtZero: true,
            grid: { color: "rgba(143, 110, 90, 0.10)" },
            title: { display: true, text: chart.metric_label || "Value" },
          },
          y1: {
            beginAtZero: true,
            max: 100,
            position: "right",
            grid: { drawOnChartArea: false },
            title: { display: true, text: "Cumulative Share %" },
            ticks: { callback: (value) => `${value}%` },
          },
        };
      }

      if (chart.axes && chart.axes.secondary_numeric) {
        options.scales = {
          y: {
            beginAtZero: true,
            grid: { color: "rgba(143, 110, 90, 0.10)" },
            title: { display: true, text: chart.left_metric_label || "Value" },
          },
          y1: {
            beginAtZero: true,
            position: "right",
            grid: { drawOnChartArea: false },
            title: { display: true, text: chart.right_metric_label || "Value" },
          },
        };
      }

      if (chart.type === "bubble") {
        options.scales = {
          x: {
            grid: { color: "rgba(143, 110, 90, 0.10)" },
            title: { display: true, text: chart.x_label || "X Value" },
          },
          y: {
            grid: { color: "rgba(143, 110, 90, 0.10)" },
            title: { display: true, text: chart.y_label || "Y Value" },
          },
        };
      } else if (!options.scales) {
        options.scales = {
          y: {
            beginAtZero: true,
            grid: { color: "rgba(143, 110, 90, 0.10)" },
            title: { display: chart.type !== "doughnut" && chart.type !== "polarArea", text: chart.metric_label || "Value" },
          },
          x: {
            grid: { display: false },
          },
        };
      }

      return options;
    };

    window.dashboardData.charts.forEach((chart) => {
      const canvas = document.getElementById(chart.id);
      if (!canvas) {
        return;
      }

      new Chart(canvas, {
        type: chart.type,
        data: {
          labels: chart.labels,
          datasets: chart.datasets,
        },
        options: buildChartOptions(chart),
      });
    });
  }

  document.querySelectorAll(".export-chart-button").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.exportTarget;
      const canvas = targetId ? document.getElementById(targetId) : null;
      if (!canvas) {
        return;
      }

      const link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = `${targetId}.png`;
      link.click();
    });
  });

  document.querySelectorAll("[data-export-pdf]").forEach((button) => {
    button.addEventListener("click", async () => {
      const selector = button.dataset.exportTarget;
      const filename = button.dataset.exportName || "report.pdf";
      const target = selector ? document.querySelector(selector) : null;
      if (!target || !window.html2canvas || !window.jspdf) {
        return;
      }

      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Preparing PDF...";

      try {
        const canvas = await window.html2canvas(target, {
          scale: 2,
          backgroundColor: "#fff8f2",
          useCORS: true,
        });

        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF("p", "mm", "a4");
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();
        const imgWidth = pageWidth - 12;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        let heightLeft = imgHeight;
        let position = 6;
        pdf.addImage(canvas.toDataURL("image/png"), "PNG", 6, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;

        while (heightLeft > 0) {
          position = heightLeft - imgHeight + 6;
          pdf.addPage();
          pdf.addImage(canvas.toDataURL("image/png"), "PNG", 6, position, imgWidth, imgHeight);
          heightLeft -= pageHeight;
        }

        pdf.save(filename);
      } finally {
        button.disabled = false;
        button.textContent = originalText;
      }
    });
  });
});
