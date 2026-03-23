import { useDroppable } from "@dnd-kit/core";

interface DroppableZoneProps {
  id: string;
  zone: string;
  accepts: string[];
  data?: Record<string, unknown>;
  children: React.ReactNode;
  className?: string;
}

export default function DroppableZone({
  id,
  zone,
  accepts,
  data,
  children,
  className = "",
}: DroppableZoneProps) {
  const { setNodeRef, isOver, active } = useDroppable({
    id,
    data: { zone, accepts, ...data },
  });

  const dragType = active?.data.current?.type as string | undefined;
  const isValidDrop = dragType ? accepts.includes(dragType) : false;
  const showActive = isOver && isValidDrop;

  return (
    <div
      ref={setNodeRef}
      className={`rounded-xl transition-all duration-200 ${
        showActive
          ? "ring-2 ring-glow/50 bg-glow/5"
          : isOver && !isValidDrop
            ? ""
            : ""
      } ${className}`}
    >
      {children}
      {showActive && (
        <div className="flex items-center justify-center h-9 mx-2 mb-2 rounded-lg border border-dashed border-glow/40 animate-pulse">
          <span className="text-xs text-glow/60">Släpp här</span>
        </div>
      )}
    </div>
  );
}
