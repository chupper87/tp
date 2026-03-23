import { useDraggable } from "@dnd-kit/core";
import { GripVertical } from "lucide-react";

interface DraggableCardProps {
  id: string;
  type: "employee" | "customer" | "measure";
  data?: Record<string, unknown>;
  children: React.ReactNode;
}

export default function DraggableCard({
  id,
  type,
  data,
  children,
}: DraggableCardProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `${type}-${id}`,
    data: { type, id, ...data },
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={`flex items-center gap-2 h-9 px-2.5 rounded-lg bg-mid/30 border border-reef/30 cursor-grab active:cursor-grabbing transition-all select-none ${
        isDragging
          ? "opacity-30 border-dashed border-glow/40"
          : "hover:border-reef-light hover:bg-mid/40"
      }`}
    >
      <GripVertical className="w-3 h-3 text-sediment shrink-0" />
      {children}
    </div>
  );
}
