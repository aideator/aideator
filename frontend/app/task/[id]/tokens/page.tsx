import TaskPageTokens from "../page-tokens"

export default function TaskPageTokensRoute({ params }: { params: Promise<{ id: string }> }) {
  return <TaskPageTokens params={params} />
}