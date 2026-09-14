interface SectionTitleProps {
  eyebrow: string;
  title: string;
  description?: string;
}

export default function SectionTitle({ eyebrow, title, description }: SectionTitleProps) {
  return (
    <div className="mb-6">
      <p className="text-xs font-black uppercase tracking-[0.28em] text-electric">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-black tracking-tight text-deepnavy sm:text-3xl">{title}</h2>
      {description && <p className="mt-3 max-w-3xl text-sm leading-6 text-slatebrand/70">{description}</p>}
    </div>
  );
}
