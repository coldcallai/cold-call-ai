const StatusBadge = ({ status }) => {
  const statusConfig = {
    new: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "New" },
    contacted: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "Contacted" },
    qualified: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Qualified" },
    not_qualified: { color: "bg-red-50 text-red-700 border-red-200", label: "Not Qualified" },
    booked: { color: "bg-purple-50 text-purple-700 border-purple-200", label: "Booked" },
    draft: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "Draft" },
    active: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Active" },
    paused: { color: "bg-amber-50 text-amber-700 border-amber-200", label: "Paused" },
    completed: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "Completed" },
    pending: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "Pending" },
    in_progress: { color: "bg-blue-50 text-blue-700 border-blue-200", label: "In Progress" },
    failed: { color: "bg-red-50 text-red-700 border-red-200", label: "Failed" },
    no_answer: { color: "bg-amber-50 text-amber-700 border-amber-200", label: "No Answer" },
  };
  
  const config = statusConfig[status] || statusConfig.new;
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}>
      {config.label}
    </span>
  );
};

export default StatusBadge;
