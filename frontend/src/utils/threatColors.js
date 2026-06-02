export const severityColors = {
  CRITICAL: { text: "text-red-400", bg: "bg-red-900/30", border: "border-red-800", dot: "#ef4444", glow: "shadow-red-glow" },
  HIGH: { text: "text-orange-400", bg: "bg-orange-900/30", border: "border-orange-800", dot: "#f97316", glow: "shadow-orange-glow" },
  MEDIUM: { text: "text-yellow-400", bg: "bg-yellow-900/30", border: "border-yellow-800", dot: "#eab308", glow: "" },
  LOW: { text: "text-green-400", bg: "bg-green-900/30", border: "border-green-800", dot: "#22c55e", glow: "" },
};

export const attackTypeColors = {
  PROMPT_INJECTION: { text: "text-red-400", label: "Prompt Injection", icon: "💉" },
  JAILBREAK: { text: "text-orange-400", label: "Jailbreak", icon: "🔓" },
  IDENTITY_SPOOFING: { text: "text-yellow-400", label: "Identity Spoofing", icon: "🎭" },
  DATA_EXFILTRATION: { text: "text-red-500", label: "Data Exfiltration", icon: "📤" },
  TOOL_ESCALATION: { text: "text-orange-500", label: "Tool Escalation", icon: "⚡" },
  SOCIAL_ENGINEERING: { text: "text-yellow-500", label: "Social Engineering", icon: "🕵️" },
  RECONNAISSANCE: { text: "text-cyan-400", label: "Reconnaissance", icon: "🔍" },
  UNKNOWN: { text: "text-gray-400", label: "Unknown", icon: "❓" },
};

export const sophisticationColors = {
  NATION_STATE: { text: "text-red-400", bg: "bg-red-900/20", label: "Nation-State" },
  ADVANCED: { text: "text-orange-400", bg: "bg-orange-900/20", label: "Advanced" },
  INTERMEDIATE: { text: "text-yellow-400", bg: "bg-yellow-900/20", label: "Intermediate" },
  SCRIPT_KIDDIE: { text: "text-green-400", bg: "bg-green-900/20", label: "Script Kiddie" },
  UNKNOWN: { text: "text-gray-400", bg: "bg-gray-900/20", label: "Unknown" },
};

export const getSeverityColor = (severity) => severityColors[severity] || severityColors.LOW;
export const getAttackColor = (type) => attackTypeColors[type] || attackTypeColors.UNKNOWN;
export const getSophisticationColor = (level) => sophisticationColors[level] || sophisticationColors.UNKNOWN;
